from pydantic import BaseModel

from app.schemas.common import GitProviderType


class PullRequestResponse(BaseModel):
    provider: GitProviderType
    repo: str
    pr_number: int
    title: str
    files_changed: int
    additions: int
    deletions: int
    diff: str
