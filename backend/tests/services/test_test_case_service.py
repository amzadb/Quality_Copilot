"""Tests for test case orchestration service."""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from app.core.errors import AppError
from app.integrations.llm import GeneratedTestCase as LLMCase, TestCaseGenerationOutput
from app.jobs.runner import JobRunner
from app.schemas.jira import JiraAttachmentRequest, JiraAttachmentResponse, JiraTicketResponse
from app.schemas.test_cases import SaveTestCasesRequest, TestCaseUpdate
from app.schemas.testrail import TestRailUploadRequest, TestRailUploadResponse
from app.services.test_case_service import TestCaseService
from tests.conftest import run_async


def _service(db_session, jira=None, llm=None, testrail=None) -> TestCaseService:
    return TestCaseService(
        db_session,
        jira or AsyncMock(),
        llm or AsyncMock(),
        testrail or AsyncMock(),
        JobRunner(),
    )


def test_generate_happy_path(db_session, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jira = AsyncMock()
    jira.fetch_ticket.return_value = JiraTicketResponse(
        key="PROJ-1042",
        title="Add SSO login flow",
        description="SSO description",
        issue_type="Story",
        url="https://acme.atlassian.net/browse/PROJ-1042",
    )
    llm = AsyncMock()
    llm.generate_test_cases.return_value = TestCaseGenerationOutput(
        test_cases=[
            LLMCase(
                id="TC-01",
                title="SSO login succeeds",
                type="functional",
                steps=["Open login", "Click SSO"],
                expected_result="Dashboard loads.",
            )
        ]
    )
    service = _service(db_session, jira=jira, llm=llm)

    response = run_async(service.generate("proj-1042"))

    assert response.ticket_key == "PROJ-1042"
    assert len(response.test_cases) == 1
    assert response.test_cases[0].id == "TC-01"
    assert response.file_paths is not None
    assert Path(response.file_paths.docx).exists()
    assert Path(response.file_paths.csv).exists()


def test_generate_marks_failed_on_jira_error(db_session, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jira = AsyncMock()
    jira.fetch_ticket.side_effect = AppError(
        status_code=404, code="JIRA_NOT_FOUND", message="missing"
    )
    service = _service(db_session, jira=jira)

    with pytest.raises(AppError) as exc:
        run_async(service.generate("PROJ-9999"))

    assert exc.value.code == "JIRA_NOT_FOUND"
    from app.models.test_case_run import TestCaseRun

    run = db_session.query(TestCaseRun).one()
    assert run.status == "failed"


def test_update_case_and_get_run(db_session, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jira = AsyncMock()
    jira.fetch_ticket.return_value = JiraTicketResponse(
        key="PROJ-1042",
        title="Title",
        description="Desc",
        issue_type="Story",
        url="https://example/browse/PROJ-1042",
    )
    llm = AsyncMock()
    llm.generate_test_cases.return_value = TestCaseGenerationOutput(
        test_cases=[
            LLMCase(
                id="TC-01",
                title="Original",
                type="functional",
                steps=["Step"],
                expected_result="OK",
            )
        ]
    )
    service = _service(db_session, jira=jira, llm=llm)
    run = run_async(service.generate("PROJ-1042"))

    updated = run_async(
        service.update_case(
            run.run_id,
            "TC-01",
            TestCaseUpdate(title="Updated title", expected_result="New expected"),
        )
    )
    assert updated.title == "Updated title"
    fetched = run_async(service.get_run(run.run_id))
    assert fetched.test_cases[0].title == "Updated title"


def test_save_attach_and_testrail_upload(db_session, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jira = AsyncMock()
    jira.fetch_ticket.return_value = JiraTicketResponse(
        key="PROJ-1042",
        title="Title",
        description="Desc",
        issue_type="Story",
        url="https://example/browse/PROJ-1042",
    )
    jira.attach_files.return_value = JiraAttachmentResponse(
        attached_files=["PROJ-1042.docx"],
        jira_attachment_ids=["10021"],
    )
    llm = AsyncMock()
    llm.generate_test_cases.return_value = TestCaseGenerationOutput(
        test_cases=[
            LLMCase(
                id="TC-01",
                title="Original",
                type="functional",
                steps=["Step"],
                expected_result="OK",
            )
        ]
    )
    testrail = AsyncMock()
    testrail.upload_run.return_value = TestRailUploadResponse(
        suite_id=12,
        testrail_case_ids=["C1044"],
        uploaded_count=1,
    )
    service = _service(db_session, jira=jira, llm=llm, testrail=testrail)
    run = run_async(service.generate("PROJ-1042"))

    saved = run_async(
        service.save_to_folder(
            run.run_id,
            SaveTestCasesRequest(folder=str(tmp_path / "export"), formats=["csv"]),
        )
    )
    assert len(saved.saved_files) == 1
    assert Path(saved.saved_files[0]).exists()

    attached = run_async(
        service.attach_to_jira(
            "PROJ-1042",
            JiraAttachmentRequest(run_id=run.run_id, file_types=["docx"], comment="hi"),
        )
    )
    assert attached.jira_attachment_ids == ["10021"]
    jira.attach_files.assert_awaited_once()

    upload = run_async(
        service.upload_to_testrail(run.run_id, TestRailUploadRequest(project_id=1, suite_id=12))
    )
    assert upload.uploaded_count == 1
    fetched = run_async(service.get_run(run.run_id))
    assert fetched.jira_attached is True
    assert fetched.testrail_uploaded is True
