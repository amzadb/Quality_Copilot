from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class TestCaseActivityItem(BaseModel):
    type: Literal["test_cases"] = "test_cases"
    ticket_key: str
    title: str
    count: int
    destination: str | None = None
    created_at: datetime


class ReviewActivityItem(BaseModel):
    type: Literal["review"] = "review"
    pr_number: int
    title: str
    count: int
    created_at: datetime


ActivityItem = TestCaseActivityItem | ReviewActivityItem


class ActivitySummary(BaseModel):
    tickets_processed: int
    test_cases_generated: int
    prs_reviewed: int
    avg_review_time_seconds: float


class ActivityResetResponse(BaseModel):
    ok: bool = True
    message: str = "Activity reset. Dashboard metrics are now zero."
