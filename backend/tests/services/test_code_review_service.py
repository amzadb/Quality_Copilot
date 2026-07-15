"""Tests for code review orchestration service."""

from unittest.mock import AsyncMock

import pytest

from app.core.errors import AppError
from app.integrations.llm import CodeReviewOutput, GeneratedReviewComment
from app.jobs.runner import JobRunner
from app.schemas.pull_requests import PullRequestResponse
from app.schemas.reviews import ReviewCommentUpdate
from app.services.code_review_service import CodeReviewService
from tests.conftest import run_async


def _service(db_session, git=None, llm=None) -> CodeReviewService:
    return CodeReviewService(
        db_session,
        git or AsyncMock(),
        llm or AsyncMock(),
        JobRunner(),
    )


def test_generate_review_happy_path(db_session):
    git = AsyncMock()
    git.fetch_pull_request.return_value = PullRequestResponse(
        provider="bitbucket",
        repo="acme/payments",
        pr_number=318,
        title="Refactor payment retry logic",
        files_changed=2,
        additions=10,
        deletions=3,
        diff="diff --git a/retry.py b/retry.py",
    )
    llm = AsyncMock()
    llm.generate_review.return_value = CodeReviewOutput(
        comments=[
            GeneratedReviewComment(
                file="retry.py",
                line=42,
                severity="high",
                comment="Retry count is not reset.",
            )
        ]
    )
    service = _service(db_session, git=git, llm=llm)

    response = run_async(service.generate("acme/payments", 318))

    assert response.pr_number == 318
    assert len(response.comments) == 1
    assert response.comments[0].severity == "high"
    assert response.comments[0].id is not None


def test_generate_review_marks_failed_on_git_error(db_session):
    git = AsyncMock()
    git.fetch_pull_request.side_effect = AppError(
        status_code=404, code="PR_NOT_FOUND", message="missing"
    )
    service = _service(db_session, git=git)

    with pytest.raises(AppError) as exc:
        run_async(service.generate("acme/payments", 999))

    assert exc.value.code == "PR_NOT_FOUND"
    from app.models.review import ReviewRun

    run = db_session.query(ReviewRun).one()
    assert run.status == "failed"


def test_update_comment_triage(db_session):
    git = AsyncMock()
    git.fetch_pull_request.return_value = PullRequestResponse(
        provider="bitbucket",
        repo="acme/payments",
        pr_number=318,
        title="Title",
        files_changed=1,
        additions=1,
        deletions=0,
        diff="diff",
    )
    llm = AsyncMock()
    llm.generate_review.return_value = CodeReviewOutput(
        comments=[
            GeneratedReviewComment(
                file="a.py",
                line=1,
                severity="medium",
                comment="style note",
            )
        ]
    )
    service = _service(db_session, git=git, llm=llm)
    run = run_async(service.generate("acme/payments", 318))
    comment_id = run.comments[0].id

    updated = run_async(
        service.update_comment(
            run.run_id,
            comment_id,
            ReviewCommentUpdate(triage_status="addressed"),
        )
    )
    assert updated.triage_status == "addressed"
    fetched = run_async(service.get_run(run.run_id))
    assert fetched.comments[0].triage_status == "addressed"
