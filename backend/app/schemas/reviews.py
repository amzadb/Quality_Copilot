from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import CommentTriageStatus, ReviewSeverity


class ReviewComment(BaseModel):
    id: str | None = None
    file: str
    line: int
    severity: ReviewSeverity
    comment: str
    triage_status: CommentTriageStatus | None = None


class ReviewCommentUpdate(BaseModel):
    triage_status: CommentTriageStatus


class GenerateReviewRequest(BaseModel):
    repo: str
    pr_number: int


class ReviewRunResponse(BaseModel):
    run_id: str
    pr_number: int
    comments: list[ReviewComment]
    created_at: datetime
