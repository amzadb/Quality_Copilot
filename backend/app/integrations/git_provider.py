"""Git provider integration — fetch PR diff/metadata, post review comments.

v1 Bitbucket auth uses Atlassian app passwords with HTTP Basic auth
(username + app password). Bearer tokens are intentionally not used.
"""

from __future__ import annotations

import re

import httpx
from fastapi import Depends

from app.core.credential_store import CredentialStore, get_credential_store
from app.core.errors import AppError
from app.integrations._http import connection_failed, connection_ok, request_json
from app.schemas.common import ConnectionTestResponse, GitProviderType
from app.schemas.pull_requests import PullRequestResponse
from app.schemas.reviews import ReviewComment


def _parse_pr_url(url: str) -> tuple[str, int]:
    cleaned = url.strip().rstrip("/")
    if "/pull-requests/" in cleaned:
        base, pr_part = cleaned.rsplit("/pull-requests/", 1)
        if pr_part.isdigit():
            repo_path = base.split("bitbucket.org/")[-1] if "bitbucket.org/" in base else base
            return repo_path.strip("/"), int(pr_part)
    if "/pull/" in cleaned:
        base, pr_part = cleaned.rsplit("/pull/", 1)
        pr_num = pr_part.split("/")[0]
        if pr_num.isdigit():
            repo_path = base.split("github.com/")[-1] if "github.com/" in base else base
            return repo_path.strip("/"), int(pr_num)
    raise AppError(
        status_code=400,
        code="INVALID_PR_URL",
        message="Could not parse pull request URL.",
    )


def _split_repo(repo: str) -> tuple[str, str]:
    parts = repo.strip("/").split("/")
    if len(parts) < 2:
        raise AppError(
            status_code=400,
            code="INVALID_REPO",
            message="Repository must be in 'workspace/repo' format.",
        )
    return parts[0], parts[1]


class GitProviderIntegration:
    def __init__(self, credentials: CredentialStore) -> None:
        self._credentials = credentials

    def _config(self) -> tuple[GitProviderType, str | None, str, str]:
        """Return provider, workspace, username, and app password."""
        section = self._credentials.get_section("git_provider")
        provider = section.get("type") or "bitbucket"
        workspace = section.get("workspace")
        username = section.get("username")
        token = section.get("token")
        if not token:
            raise AppError(
                status_code=400,
                code="GIT_NOT_CONFIGURED",
                message="Git provider is not configured. Set an app password in Settings.",
            )
        if provider == "bitbucket" and not username:
            raise AppError(
                status_code=400,
                code="GIT_NOT_CONFIGURED",
                message=(
                    "Bitbucket app-password auth requires a username. "
                    "Set Atlassian account username in Settings."
                ),
            )
        return provider, workspace, username or "", token

    def _auth(self, username: str, token: str) -> tuple[str, str]:
        """Bitbucket app passwords use Basic auth (username + app password)."""
        return username, token

    def _resolve_repo(
        self,
        *,
        repo: str | None,
        pr_number: int | None,
        url: str | None,
        workspace: str | None,
    ) -> tuple[str, int]:
        if url:
            parsed_repo, parsed_pr = _parse_pr_url(url)
            return parsed_repo, parsed_pr
        if repo and pr_number is not None:
            if "/" not in repo and workspace:
                return f"{workspace}/{repo}", pr_number
            return repo, pr_number
        raise AppError(
            status_code=400,
            code="INVALID_PR_REQUEST",
            message="Provide either a PR URL or repo and pr_number.",
        )

    async def fetch_pull_request(
        self,
        *,
        repo: str | None = None,
        pr_number: int | None = None,
        url: str | None = None,
    ) -> PullRequestResponse:
        provider, workspace, username, token = self._config()
        full_repo, pr_num = self._resolve_repo(
            repo=repo, pr_number=pr_number, url=url, workspace=workspace
        )

        if provider != "bitbucket":
            raise AppError(
                status_code=501,
                code="GIT_PROVIDER_UNSUPPORTED",
                message=f"Provider '{provider}' is not implemented yet. Bitbucket is supported in v1.",
            )

        workspace_slug, repo_slug = _split_repo(full_repo)
        api_base = "https://api.bitbucket.org/2.0"
        pr_url = (
            f"{api_base}/repositories/{workspace_slug}/{repo_slug}/pullrequests/{pr_num}"
        )
        auth = self._auth(username, token)

        try:
            payload = await request_json("GET", pr_url, auth=auth)
            diff_text = await self._fetch_bitbucket_diff(
                api_base, workspace_slug, repo_slug, pr_num, auth
            )
        except AppError as exc:
            if exc.code == "NOT_FOUND":
                raise AppError(
                    status_code=404,
                    code="PR_NOT_FOUND",
                    message=f"Pull request #{pr_num} was not found in {full_repo}.",
                ) from exc
            if exc.code == "AUTH_FAILED":
                raise AppError(
                    status_code=401,
                    code="GIT_AUTH_FAILED",
                    message="Git provider authentication failed. Check username and app password.",
                ) from exc
            raise

        stats = self._extract_diff_stats(diff_text)
        return PullRequestResponse(
            provider="bitbucket",
            repo=full_repo,
            pr_number=pr_num,
            title=payload.get("title", ""),
            files_changed=stats["files_changed"],
            additions=stats["additions"],
            deletions=stats["deletions"],
            diff=diff_text,
        )

    async def _fetch_bitbucket_diff(
        self,
        api_base: str,
        workspace: str,
        repo_slug: str,
        pr_number: int,
        auth: tuple[str, str],
    ) -> str:
        diff_url = (
            f"{api_base}/repositories/{workspace}/{repo_slug}/pullrequests/{pr_number}/diff"
        )
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                diff_url,
                auth=auth,
                headers={"Accept": "text/plain"},
            )
        if response.status_code >= 400:
            raise AppError(
                status_code=502,
                code="GIT_DIFF_FAILED",
                message=f"Failed to fetch pull request diff (HTTP {response.status_code}).",
            )
        return response.text

    @staticmethod
    def _extract_diff_stats(diff_text: str) -> dict[str, int]:
        files = len(re.findall(r"^diff --git ", diff_text, flags=re.MULTILINE))
        additions = len(re.findall(r"^\+[^+]", diff_text, flags=re.MULTILINE))
        deletions = len(re.findall(r"^-[^-]", diff_text, flags=re.MULTILINE))
        return {
            "files_changed": files,
            "additions": additions,
            "deletions": deletions,
        }

    async def post_review_comments(
        self, repo: str, pr_number: int, comments: list[ReviewComment]
    ) -> None:
        provider, _, username, token = self._config()
        if provider != "bitbucket":
            raise AppError(
                status_code=501,
                code="GIT_PROVIDER_UNSUPPORTED",
                message=f"Provider '{provider}' is not implemented yet.",
            )

        workspace_slug, repo_slug = _split_repo(repo)
        api_base = "https://api.bitbucket.org/2.0"
        url = (
            f"{api_base}/repositories/{workspace_slug}/{repo_slug}/pullrequests/"
            f"{pr_number}/comments"
        )
        auth = self._auth(username, token)

        for comment in comments:
            content = comment.comment
            if comment.file:
                content = f"{comment.file}:{comment.line}\n\n{content}"
            body = {"content": {"raw": content}}
            await request_json("POST", url, auth=auth, json=body)

    async def test_connection(self) -> ConnectionTestResponse:
        try:
            provider, _, username, token = self._config()
        except AppError as exc:
            return connection_failed(exc.code, str(exc.detail))

        if provider != "bitbucket":
            return connection_failed(
                "GIT_PROVIDER_UNSUPPORTED",
                f"Connection test for '{provider}' is not implemented yet.",
            )

        url = "https://api.bitbucket.org/2.0/user"
        try:
            await request_json("GET", url, auth=self._auth(username, token))
        except AppError as exc:
            if exc.code == "AUTH_FAILED":
                return connection_failed(
                    "GIT_AUTH_FAILED",
                    "Git provider authentication failed. Check username and app password.",
                )
            return connection_failed("GIT_CONNECTION_FAILED", str(exc.detail))
        except httpx.HTTPError as exc:
            return connection_failed("GIT_CONNECTION_FAILED", str(exc))

        return connection_ok()


def get_git_provider_integration(
    credentials: CredentialStore = Depends(get_credential_store),
) -> GitProviderIntegration:
    return GitProviderIntegration(credentials)
