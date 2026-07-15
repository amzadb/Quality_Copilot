"""Test case generation orchestration — JIRA → LLM → export → TestRail."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.integrations.jira import JiraIntegration, get_jira_integration
from app.integrations.llm import LLMIntegration, get_llm_integration
from app.integrations.testrail import TestRailIntegration, get_testrail_integration
from app.jobs.runner import JobRunner, get_job_runner
from app.models.base import get_db
from app.models.test_case_run import GeneratedTestCase, TestCaseRun
from app.models.ticket import Ticket
from app.schemas.jira import JiraAttachmentRequest, JiraAttachmentResponse
from app.schemas.test_cases import (
    FilePaths,
    SaveTestCasesRequest,
    SaveTestCasesResponse,
    TestCase,
    TestCaseRunResponse,
    TestCaseUpdate,
)
from app.schemas.testrail import TestRailUploadRequest, TestRailUploadResponse
from app.services.exporters import default_export_dir, export_cases, read_export_bytes


class TestCaseService:
    """Orchestrates ticket fetch, LLM generation, local export, JIRA attach, and TestRail upload."""

    def __init__(
        self,
        db: Session,
        jira: JiraIntegration,
        llm: LLMIntegration,
        testrail: TestRailIntegration,
        job_runner: JobRunner,
    ) -> None:
        self._db = db
        self._jira = jira
        self._llm = llm
        self._testrail = testrail
        self._jobs = job_runner

    async def generate(self, ticket_key: str) -> TestCaseRunResponse:
        key = ticket_key.strip().upper()
        run = TestCaseRun(ticket_key=key, status="pending")
        self._db.add(run)
        self._db.commit()
        self._db.refresh(run)

        try:
            ticket = await self._jira.fetch_ticket(key)
            self._upsert_ticket(ticket)

            llm_output = await self._llm.generate_test_cases(ticket)
            cases = [
                TestCase(
                    id=item.id,
                    title=item.title,
                    type=item.type,
                    steps=item.steps,
                    expected_result=item.expected_result,
                )
                for item in llm_output.test_cases
            ]
            for case in cases:
                self._db.add(
                    GeneratedTestCase(
                        id=case.id,
                        run_id=run.id,
                        title=case.title,
                        type=case.type,
                        steps=case.steps,
                        expected_result=case.expected_result,
                    )
                )

            paths = export_cases(
                default_export_dir(key),
                key,
                cases,
                formats=["docx", "csv"],
            )
            run.file_paths = paths
            run.status = "completed"
            self._db.commit()
            self._db.refresh(run)
            return self._to_response(run, cases)
        except Exception:
            self._db.rollback()
            failed = self._db.get(TestCaseRun, run.id)
            if failed is not None:
                failed.status = "failed"
                self._db.commit()
            raise

    async def get_run(self, run_id: str) -> TestCaseRunResponse:
        run = self._require_run(run_id)
        return self._to_response(run, self._cases_from_run(run))

    async def update_case(self, run_id: str, case_id: str, update: TestCaseUpdate) -> TestCase:
        run_uuid = self._parse_run_id(run_id)
        case = self._db.get(GeneratedTestCase, {"run_id": run_uuid, "id": case_id})
        if case is None:
            raise AppError(
                status_code=404,
                code="TEST_CASE_NOT_FOUND",
                message=f"Test case '{case_id}' was not found in run '{run_id}'.",
            )

        payload = update.model_dump(exclude_none=True)
        for field, value in payload.items():
            setattr(case, field, value)
        self._db.commit()
        self._db.refresh(case)
        return TestCase(
            id=case.id,
            title=case.title,
            type=case.type,  # type: ignore[arg-type]
            steps=list(case.steps),
            expected_result=case.expected_result,
        )

    async def save_to_folder(self, run_id: str, request: SaveTestCasesRequest) -> SaveTestCasesResponse:
        run = self._require_run(run_id)
        cases = self._cases_from_run(run)
        folder = Path(request.folder)
        saved = export_cases(folder, run.ticket_key, cases, list(request.formats))
        paths = dict(run.file_paths or {})
        paths.update(saved)
        run.file_paths = paths
        self._db.commit()
        return SaveTestCasesResponse(saved_files=list(saved.values()))

    async def get_download_path(self, run_id: str, format: str) -> str:
        run = self._require_run(run_id)
        paths = run.file_paths or {}
        path = paths.get(format)
        if not path or not Path(path).exists():
            cases = self._cases_from_run(run)
            exported = export_cases(
                default_export_dir(run.ticket_key),
                run.ticket_key,
                cases,
                formats=[format],
            )
            path = exported.get(format)
            if not path:
                raise AppError(
                    status_code=404,
                    code="EXPORT_NOT_FOUND",
                    message=f"No {format} export found for run '{run_id}'.",
                )
            paths = dict(paths)
            paths[format] = path
            run.file_paths = paths
            self._db.commit()
        return str(path)

    async def attach_to_jira(
        self, ticket_key: str, body: JiraAttachmentRequest
    ) -> JiraAttachmentResponse:
        run = self._require_run(body.run_id)
        files: list[tuple[str, bytes]] = []
        for fmt in body.file_types:
            path = await self.get_download_path(str(run.id), fmt)
            files.append((Path(path).name, read_export_bytes(Path(path))))

        response = await self._jira.attach_files(ticket_key, body, files=files)
        run.jira_attached = True
        self._db.commit()
        return response

    async def upload_to_testrail(
        self, run_id: str, request: TestRailUploadRequest
    ) -> TestRailUploadResponse:
        run = self._require_run(run_id)
        cases = self._cases_from_run(run)
        response = await self._testrail.upload_run(cases, request)
        run.testrail_uploaded = True
        run.testrail_case_ids = response.testrail_case_ids
        self._db.commit()
        return response

    def _upsert_ticket(self, ticket) -> None:
        existing = self._db.query(Ticket).filter_by(jira_key=ticket.key).one_or_none()
        if existing is None:
            existing = Ticket(jira_key=ticket.key)
            self._db.add(existing)
        existing.title = ticket.title
        existing.description = ticket.description
        existing.acceptance_criteria = ticket.acceptance_criteria
        existing.issue_type = ticket.issue_type
        existing.url = ticket.url
        self._db.flush()

    def _parse_run_id(self, run_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(run_id)
        except ValueError as exc:
            raise AppError(
                status_code=404,
                code="RUN_NOT_FOUND",
                message=f"Test case run '{run_id}' was not found.",
            ) from exc

    def _require_run(self, run_id: str) -> TestCaseRun:
        run = (
            self._db.query(TestCaseRun)
            .options(joinedload(TestCaseRun.test_cases))
            .filter(TestCaseRun.id == self._parse_run_id(run_id))
            .one_or_none()
        )
        if run is None:
            raise AppError(
                status_code=404,
                code="RUN_NOT_FOUND",
                message=f"Test case run '{run_id}' was not found.",
            )
        return run

    @staticmethod
    def _cases_from_run(run: TestCaseRun) -> list[TestCase]:
        return [
            TestCase(
                id=case.id,
                title=case.title,
                type=case.type,  # type: ignore[arg-type]
                steps=list(case.steps),
                expected_result=case.expected_result,
            )
            for case in sorted(run.test_cases, key=lambda item: item.id)
        ]

    @staticmethod
    def _to_response(run: TestCaseRun, cases: list[TestCase]) -> TestCaseRunResponse:
        file_paths = None
        if run.file_paths:
            file_paths = FilePaths(
                docx=run.file_paths.get("docx"),
                csv=run.file_paths.get("csv"),
            )
        return TestCaseRunResponse(
            run_id=str(run.id),
            ticket_key=run.ticket_key,
            test_cases=cases,
            created_at=run.created_at,
            file_paths=file_paths,
            jira_attached=run.jira_attached,
            testrail_uploaded=run.testrail_uploaded,
            testrail_case_ids=run.testrail_case_ids,
        )


def get_test_case_service(
    db: Session = Depends(get_db),
    jira: JiraIntegration = Depends(get_jira_integration),
    llm: LLMIntegration = Depends(get_llm_integration),
    testrail: TestRailIntegration = Depends(get_testrail_integration),
    job_runner: JobRunner = Depends(get_job_runner),
) -> TestCaseService:
    return TestCaseService(db, jira, llm, testrail, job_runner)
