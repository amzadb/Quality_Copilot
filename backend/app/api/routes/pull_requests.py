from fastapi import APIRouter, Depends, Query

from app.integrations.git_provider import GitProviderIntegration, get_git_provider_integration
from app.schemas.pull_requests import PullRequestResponse

router = APIRouter()


@router.get("", response_model=PullRequestResponse)
async def get_pull_request(
    repo: str | None = Query(default=None),
    pr_number: int | None = Query(default=None),
    url: str | None = Query(default=None),
    git: GitProviderIntegration = Depends(get_git_provider_integration),
) -> PullRequestResponse:
    return await git.fetch_pull_request(repo=repo, pr_number=pr_number, url=url)
