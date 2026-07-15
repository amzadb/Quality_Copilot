"""Tests for dashboard activity service."""

from datetime import datetime, timezone

from app.models.pull_request import PullRequestRecord
from app.models.review import ReviewCommentRecord, ReviewRun
from app.models.test_case_run import GeneratedTestCase, TestCaseRun
from app.models.ticket import Ticket
from app.services.activity_service import ActivityService
from tests.conftest import run_async


def test_recent_and_summary(db_session):
    ticket = Ticket(jira_key="PROJ-1042", title="Add SSO login flow")
    run = TestCaseRun(
        ticket_key="PROJ-1042",
        status="completed",
        testrail_uploaded=True,
        created_at=datetime.now(timezone.utc),
    )
    run.test_cases.append(
        GeneratedTestCase(
            id="TC-01",
            title="Case",
            type="functional",
            steps=["a"],
            expected_result="b",
        )
    )
    pr = PullRequestRecord(
        provider="bitbucket",
        repo="acme/payments",
        pr_number=318,
        title="Refactor payment retry logic",
        files_changed=2,
        additions=5,
        deletions=1,
    )
    review = ReviewRun(
        repo="acme/payments",
        pr_number=318,
        status="completed",
        duration_seconds=42.0,
        created_at=datetime.now(timezone.utc),
    )
    review.comments.append(
        ReviewCommentRecord(
            file="retry.py",
            line=1,
            severity="high",
            comment="Issue",
        )
    )
    db_session.add_all([ticket, run, pr, review])
    db_session.commit()

    service = ActivityService(db_session)
    recent = run_async(service.get_recent(limit=10))
    summary = run_async(service.get_summary())

    assert len(recent) == 2
    assert {item.type for item in recent} == {"test_cases", "review"}
    test_item = next(item for item in recent if item.type == "test_cases")
    assert test_item.title == "Add SSO login flow"
    assert test_item.destination == "testrail"
    review_item = next(item for item in recent if item.type == "review")
    assert review_item.title == "Refactor payment retry logic"

    assert summary.tickets_processed == 1
    assert summary.test_cases_generated == 1
    assert summary.prs_reviewed == 1
    assert summary.avg_review_time_seconds == 42.0
