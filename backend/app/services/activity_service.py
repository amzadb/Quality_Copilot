"""Dashboard activity feed backed by persisted run history."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.base import get_db
from app.models.pull_request import PullRequestRecord
from app.models.review import ReviewCommentRecord, ReviewRun
from app.models.test_case_run import GeneratedTestCase, TestCaseRun
from app.models.ticket import Ticket
from app.schemas.activity import (
    ActivityItem,
    ActivityResetResponse,
    ActivitySummary,
    ReviewActivityItem,
    TestCaseActivityItem,
)


class ActivityService:
    def __init__(self, db: Session) -> None:
        self._db = db

    async def get_recent(self, limit: int = 20) -> list[ActivityItem]:
        test_runs = (
            self._db.query(TestCaseRun)
            .options(joinedload(TestCaseRun.test_cases))
            .order_by(TestCaseRun.created_at.desc())
            .limit(limit)
            .all()
        )
        review_runs = (
            self._db.query(ReviewRun)
            .options(joinedload(ReviewRun.comments))
            .order_by(ReviewRun.created_at.desc())
            .limit(limit)
            .all()
        )

        ticket_keys = {run.ticket_key for run in test_runs}
        ticket_titles: dict[str, str] = {}
        if ticket_keys:
            ticket_titles = {
                ticket.jira_key: ticket.title
                for ticket in self._db.query(Ticket).filter(Ticket.jira_key.in_(ticket_keys)).all()
            }

        pr_titles: dict[tuple[str, int], str] = {}
        if review_runs:
            pr_records = (
                self._db.query(PullRequestRecord)
                .filter(
                    PullRequestRecord.repo.in_({run.repo for run in review_runs}),
                )
                .all()
            )
            pr_titles = {(record.repo, record.pr_number): record.title for record in pr_records}

        items: list[ActivityItem] = []
        for run in test_runs:
            destination = None
            if run.testrail_uploaded:
                destination = "testrail"
            elif run.jira_attached:
                destination = "jira"
            items.append(
                TestCaseActivityItem(
                    ticket_key=run.ticket_key,
                    title=ticket_titles.get(run.ticket_key, run.ticket_key),
                    count=len(run.test_cases),
                    destination=destination,
                    created_at=run.created_at,
                )
            )

        for run in review_runs:
            items.append(
                ReviewActivityItem(
                    pr_number=run.pr_number,
                    title=pr_titles.get((run.repo, run.pr_number), f"{run.repo}#{run.pr_number}"),
                    count=len(run.comments),
                    created_at=run.created_at,
                )
            )

        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    async def get_summary(self) -> ActivitySummary:
        tickets_processed = self._db.query(func.count(func.distinct(TestCaseRun.ticket_key))).scalar() or 0
        test_cases_generated = self._db.query(func.count()).select_from(GeneratedTestCase).scalar() or 0
        prs_reviewed = self._db.query(func.count(ReviewRun.id)).scalar() or 0
        avg_review = (
            self._db.query(func.avg(ReviewRun.duration_seconds))
            .filter(ReviewRun.duration_seconds.is_not(None))
            .scalar()
        )
        return ActivitySummary(
            tickets_processed=int(tickets_processed),
            test_cases_generated=int(test_cases_generated),
            prs_reviewed=int(prs_reviewed),
            avg_review_time_seconds=float(avg_review or 0.0),
        )

    async def reset_activity(self) -> ActivityResetResponse:
        """Clear run history that feeds dashboard summary and recent activity."""
        # Delete children first — SQLite may not enforce ON DELETE CASCADE via bulk ORM deletes.
        self._db.query(ReviewCommentRecord).delete()
        self._db.query(ReviewRun).delete()
        self._db.query(GeneratedTestCase).delete()
        self._db.query(TestCaseRun).delete()
        self._db.commit()
        return ActivityResetResponse()


def get_activity_service(db: Session = Depends(get_db)) -> ActivityService:
    return ActivityService(db)
