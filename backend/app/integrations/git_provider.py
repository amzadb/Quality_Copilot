"""Git provider integration — fetch PR diff/metadata, post review comments."""

from app.core.errors import not_implemented_yet
from app.schemas.common import ConnectionTestResponse
from app.schemas.pull_requests import PullRequestResponse
from app.schemas.reviews import ReviewComment


class GitProviderIntegration:
    async def fetch_pull_request(
        self,
        *,
        repo: str | None = None,
        pr_number: int | None = None,
        url: str | None = None,
    ) -> PullRequestResponse:
        target = url or f"{repo}#{pr_number}"
        not_implemented_yet(
            "Pull request fetch",
            f"Fetching pull request '{target}' is not implemented yet.",
        )

    async def post_review_comments(
        self, repo: str, pr_number: int, comments: list[ReviewComment]
    ) -> None:
        not_implemented_yet(
            "PR review comment post",
            f"Posting review comments to {repo} PR #{pr_number} is not implemented yet.",
        )

    async def test_connection(self) -> ConnectionTestResponse:
        not_implemented_yet(
            "Git provider connection test",
            "Testing the Git provider integration is not implemented yet.",
        )


def get_git_provider_integration() -> GitProviderIntegration:
    return GitProviderIntegration()
