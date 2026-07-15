"""Code review orchestration — Git provider → LLM → persist → comment triage."""

from __future__ import annotations

import time
import uuid

from fastapi import Depends
from sqlalchemy.orm import Session, joinedload

from app.core.errors import AppError
from app.integrations.git_provider import GitProviderIntegration, get_git_provider_integration
from app.integrations.llm import LLMIntegration, get_llm_integration
from app.jobs.runner import JobRunner, get_job_runner
from app.models.base import get_db
from app.models.pull_request import PullRequestRecord
from app.models.review import ReviewCommentRecord, ReviewRun
from app.schemas.reviews import ReviewComment, ReviewCommentUpdate, ReviewRunResponse


class CodeReviewService:
    """Orchestrates PR fetch, LLM review, run persistence, and comment triage."""

    def __init__(
        self,
        db: Session,
        git: GitProviderIntegration,
        llm: LLMIntegration,
        job_runner: JobRunner,
    ) -> None:
        self._db = db
        self._git = git
        self._llm = llm
        self._jobs = job_runner

    async def generate(self, repo: str, pr_number: int) -> ReviewRunResponse:
        started = time.perf_counter()
        run = ReviewRun(repo=repo, pr_number=pr_number, status="pending")
        self._db.add(run)
        self._db.commit()
        self._db.refresh(run)

        try:
            pull_request = await self._git.fetch_pull_request(repo=repo, pr_number=pr_number)
            self._upsert_pull_request(pull_request)

            llm_output = await self._llm.generate_review(pull_request)
            for item in llm_output.comments:
                self._db.add(
                    ReviewCommentRecord(
                        run_id=run.id,
                        file=item.file,
                        line=item.line,
                        severity=item.severity,
                        comment=item.comment,
                    )
                )

            run.status = "completed"
            run.duration_seconds = time.perf_counter() - started
            self._db.commit()
            return self._to_response(self._require_run(str(run.id)))
        except Exception:
            self._db.rollback()
            failed = self._db.get(ReviewRun, run.id)
            if failed is not None:
                failed.status = "failed"
                failed.duration_seconds = time.perf_counter() - started
                self._db.commit()
            raise

    async def get_run(self, run_id: str) -> ReviewRunResponse:
        return self._to_response(self._require_run(run_id))

    async def update_comment(
        self, run_id: str, comment_id: str, update: ReviewCommentUpdate
    ) -> ReviewComment:
        run = self._require_run(run_id)
        try:
            comment_uuid = uuid.UUID(comment_id)
        except ValueError as exc:
            raise AppError(
                status_code=404,
                code="COMMENT_NOT_FOUND",
                message=f"Review comment '{comment_id}' was not found.",
            ) from exc

        comment = next((item for item in run.comments if item.id == comment_uuid), None)
        if comment is None:
            raise AppError(
                status_code=404,
                code="COMMENT_NOT_FOUND",
                message=f"Review comment '{comment_id}' was not found in run '{run_id}'.",
            )

        comment.triage_status = update.triage_status
        self._db.commit()
        self._db.refresh(comment)
        return ReviewComment(
            id=str(comment.id),
            file=comment.file,
            line=comment.line,
            severity=comment.severity,  # type: ignore[arg-type]
            comment=comment.comment,
            triage_status=comment.triage_status,  # type: ignore[arg-type]
        )

    def _upsert_pull_request(self, pull_request) -> None:
        existing = (
            self._db.query(PullRequestRecord)
            .filter_by(repo=pull_request.repo, pr_number=pull_request.pr_number)
            .one_or_none()
        )
        if existing is None:
            existing = PullRequestRecord(
                provider=pull_request.provider,
                repo=pull_request.repo,
                pr_number=pull_request.pr_number,
            )
            self._db.add(existing)

        existing.provider = pull_request.provider
        existing.title = pull_request.title
        existing.files_changed = pull_request.files_changed
        existing.additions = pull_request.additions
        existing.deletions = pull_request.deletions
        existing.diff = pull_request.diff
        self._db.flush()

    def _parse_run_id(self, run_id: str) -> uuid.UUID:
        try:
            return uuid.UUID(run_id)
        except ValueError as exc:
            raise AppError(
                status_code=404,
                code="RUN_NOT_FOUND",
                message=f"Review run '{run_id}' was not found.",
            ) from exc

    def _require_run(self, run_id: str) -> ReviewRun:
        run = (
            self._db.query(ReviewRun)
            .options(joinedload(ReviewRun.comments))
            .filter(ReviewRun.id == self._parse_run_id(run_id))
            .one_or_none()
        )
        if run is None:
            raise AppError(
                status_code=404,
                code="RUN_NOT_FOUND",
                message=f"Review run '{run_id}' was not found.",
            )
        return run

    @staticmethod
    def _to_response(run: ReviewRun) -> ReviewRunResponse:
        comments = [
            ReviewComment(
                id=str(comment.id),
                file=comment.file,
                line=comment.line,
                severity=comment.severity,  # type: ignore[arg-type]
                comment=comment.comment,
                triage_status=comment.triage_status,  # type: ignore[arg-type]
            )
            for comment in run.comments
        ]
        return ReviewRunResponse(
            run_id=str(run.id),
            pr_number=run.pr_number,
            comments=comments,
            created_at=run.created_at,
        )


def get_code_review_service(
    db: Session = Depends(get_db),
    git: GitProviderIntegration = Depends(get_git_provider_integration),
    llm: LLMIntegration = Depends(get_llm_integration),
    job_runner: JobRunner = Depends(get_job_runner),
) -> CodeReviewService:
    return CodeReviewService(db, git, llm, job_runner)
