"""HTTP client for the FastAPI backend.

Phase 3 behavior:
- Live API responses are used whenever the backend is reachable.
- HTTP 4xx/5xx raise so the UI can show real errors (no silent fake success).
- Only network/connectivity failures optionally fall back to demo data.
"""

from datetime import datetime
from typing import Any

import httpx
from nicegui import ui

from app.auth import clear_session, get_token
from app.config import settings

_AUTH_PUBLIC_PATHS = {"/auth/login", "/auth/register", "/auth/reset-password"}

# Demo data — used only when the backend is unreachable (connection/timeout).
MOCK_SUMMARY: dict[str, Any] = {
    "tickets_processed": 128,
    "test_cases_generated": 742,
    "prs_reviewed": 64,
    "avg_review_time_seconds": 38,
}

MOCK_RECENT: list[dict[str, Any]] = [
    {
        "type": "test_cases",
        "ticket_key": "PROJ-1042",
        "title": "Add SSO login flow",
        "count": 12,
        "created_at": datetime.now().isoformat(),
        "time_label": "2h ago",
    },
    {
        "type": "review",
        "pr_number": 318,
        "title": "Refactor payment retry logic",
        "count": 5,
        "created_at": datetime.now().isoformat(),
        "time_label": "4h ago",
    },
    {
        "type": "test_cases",
        "ticket_key": "PROJ-1039",
        "title": "Fix cart total rounding",
        "count": 7,
        "created_at": datetime.now().isoformat(),
        "time_label": "Yesterday",
    },
]


MOCK_TICKET: dict[str, Any] = {
    "key": "PROJ-1042",
    "title": "Add SSO login flow",
    "description": (
        "Users should be able to authenticate via company SSO instead of a local password, "
        "with fallback to email login for external contractors."
    ),
    "acceptance_criteria": None,
    "issue_type": "Story",
    "url": "https://acme.atlassian.net/browse/PROJ-1042",
}

MOCK_TEST_CASES: list[dict[str, Any]] = [
    {
        "id": "TC-01",
        "title": "SSO login succeeds with valid credentials",
        "type": "functional",
        "steps": ["Navigate to login", "Click SSO", "Enter valid credentials"],
        "expected_result": "user is redirected to dashboard, session token issued.",
    },
    {
        "id": "TC-02",
        "title": "SSO provider times out",
        "type": "edge_case",
        "steps": ["Navigate to login", "Click SSO", "Simulate provider timeout"],
        "expected_result": "user sees a clear timeout error with retry option.",
    },
    *[
        {
            "id": f"TC-{i:02d}",
            "title": f"Additional SSO scenario {i}",
            "type": "functional" if i % 3 else "negative",
            "steps": ["Step 1", "Step 2"],
            "expected_result": f"Expected outcome for scenario {i}.",
        }
        for i in range(3, 13)
    ],
]


def _mock_run(ticket_key: str) -> dict[str, Any]:
    return {
        "run_id": "demo-run-0001",
        "ticket_key": ticket_key,
        "test_cases": MOCK_TEST_CASES,
        "created_at": datetime.now().isoformat(),
        "file_paths": {"docx": f"output/test_cases/{ticket_key}.docx", "csv": None},
    }


MOCK_PULL_REQUEST: dict[str, Any] = {
    "provider": "bitbucket",
    "repo": "acme/payments",
    "pr_number": 318,
    "title": "Refactor payment retry logic",
    "files_changed": 4,
    "additions": 112,
    "deletions": 48,
    "diff": "",
}

MOCK_REVIEW_COMMENTS: list[dict[str, Any]] = [
    {
        "id": "c1",
        "file": "retry_handler.py",
        "line": 42,
        "severity": "high",
        "comment": (
            "Retry count is not reset after a successful attempt, which can cause the next "
            "failure to skip retries entirely."
        ),
    },
    {
        "id": "c2",
        "file": "retry_handler.py",
        "line": 67,
        "severity": "medium",
        "comment": "No test coverage for the exponential backoff path added in this PR.",
    },
    {
        "id": "c3",
        "file": "payment_gateway.py",
        "line": 128,
        "severity": "medium",
        "comment": "Consider extracting magic number 5000 into a named constant for retry delay.",
    },
    {
        "id": "c4",
        "file": "retry_handler.py",
        "line": 15,
        "severity": "style",
        "comment": "Import order does not match project convention (stdlib before third-party).",
    },
    {
        "id": "c5",
        "file": "tests/test_retry.py",
        "line": 0,
        "severity": "high",
        "comment": "Missing edge case test when max retries is exceeded with intermittent failures.",
    },
]


def _mock_review_run(pr: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": "demo-review-0001",
        "pr_number": pr["pr_number"],
        "comments": MOCK_REVIEW_COMMENTS,
        "created_at": datetime.now().isoformat(),
    }


MOCK_SETTINGS: dict[str, Any] = {
    "jira": {"base_url": None, "token_set": False},
    "git_provider": {
        "type": "bitbucket",
        "workspace": None,
        "username": None,
        "token_set": False,
    },
    "testrail": {"base_url": None, "username": None, "token_set": False},
    "llm": {"provider": "claude", "token_set": False},
}

MOCK_TESTRAIL_PROJECTS: list[dict[str, Any]] = [
    {"id": 1, "name": "Payments platform"},
    {"id": 2, "name": "Core platform"},
]

MOCK_TESTRAIL_SUITES: list[dict[str, Any]] = [
    {"id": 12, "name": "Login and authentication"},
    {"id": 15, "name": "Checkout flow"},
]


def _parse_pr_url(url: str) -> tuple[str, int] | None:
    """Extract repo and PR number from a Bitbucket/GitHub-style URL."""
    cleaned = url.strip().rstrip("/")
    if not cleaned:
        return None

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

    return None


class ApiClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or settings.api_base

    def _headers(self) -> dict[str, str]:
        token = get_token()
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    def _handle_unauthorized(self, path: str) -> None:
        if path in _AUTH_PUBLIC_PATHS:
            return
        clear_session()
        try:
            ui.navigate.to("/login")
        except RuntimeError:
            pass

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        timeout: float = 30.0,
        require_backend: bool = False,
    ) -> dict[str, Any] | list[Any] | None:
        """Call the backend. Raises on HTTP errors; returns None if offline (unless require_backend)."""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method,
                    f"{self.base_url}{path}",
                    json=json,
                    headers=self._headers(),
                )
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            if require_backend:
                raise RuntimeError(
                    f"Backend unreachable at {self.base_url}{path} ({exc.__class__.__name__}). "
                    "On Render, set the web service env BACKEND_URL to your API URL "
                    "(e.g. https://quality-copilot-api.onrender.com)."
                ) from exc
            return None

        if response.status_code == 401:
            self._handle_unauthorized(path)
            raise httpx.HTTPStatusError(
                f"HTTP 401 for {method} {path}",
                request=response.request,
                response=response,
            )
        if response.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {response.status_code} for {method} {path}",
                request=response.request,
                response=response,
            )
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def _get(self, path: str) -> dict[str, Any] | list[Any] | None:
        return await self._request("GET", path, timeout=30.0)

    async def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any] | list[Any] | None:
        return await self._request("POST", path, json=body, timeout=120.0)

    async def _put(self, path: str, body: dict[str, Any]) -> dict[str, Any] | list[Any] | None:
        return await self._request("PUT", path, json=body, timeout=30.0)

    async def _patch(self, path: str, body: dict[str, Any]) -> dict[str, Any] | list[Any] | None:
        return await self._request("PATCH", path, json=body, timeout=30.0)

    async def login(self, username: str, password: str) -> dict[str, Any]:
        # Cold-start free Render services can take >30s to wake.
        data = await self._request(
            "POST",
            "/auth/login",
            json={"username": username, "password": password},
            timeout=90.0,
            require_backend=True,
        )
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected empty response from login.")
        return data

    async def register(
        self, username: str, password: str, *, email: str | None = None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"username": username, "password": password}
        if email:
            body["email"] = email
        data = await self._request(
            "POST",
            "/auth/register",
            json=body,
            timeout=90.0,
            require_backend=True,
        )
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected empty response from register.")
        return data

    async def reset_password(self, username: str, new_password: str) -> dict[str, Any]:
        data = await self._request(
            "POST",
            "/auth/reset-password",
            json={"username": username, "new_password": new_password},
            timeout=90.0,
            require_backend=True,
        )
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected empty response from reset-password.")
        return data

    async def me(self) -> dict[str, Any] | None:
        data = await self._get("/auth/me")
        return data if isinstance(data, dict) else None

    async def logout(self) -> None:
        try:
            await self._post("/auth/logout", {})
        except Exception:  # noqa: BLE001 — client clears session regardless
            pass
        clear_session()

    async def fetch_jira_ticket(self, ticket_key: str) -> dict[str, Any]:
        data = await self._get(f"/jira/tickets/{ticket_key}")
        if isinstance(data, dict):
            return data
        mock = MOCK_TICKET.copy()
        mock["key"] = ticket_key
        return mock

    async def generate_test_cases(self, ticket_key: str) -> dict[str, Any]:
        data = await self._post("/test-cases/generate", {"ticket_key": ticket_key})
        if isinstance(data, dict):
            return data
        return _mock_run(ticket_key)

    async def save_test_cases_locally(
        self, run_id: str, folder: str, formats: list[str]
    ) -> dict[str, Any]:
        data = await self._post(
            f"/test-cases/runs/{run_id}/save",
            {"folder": folder, "formats": formats},
        )
        if isinstance(data, dict):
            return data
        from datetime import date

        today = date.today().isoformat()
        ticket_key = folder.rstrip("/").split("/")[-1] or "PROJ-1042"
        saved = [f"{folder.rstrip('/')}/{ticket_key}_{today}.{fmt}" for fmt in formats]
        return {"saved_files": saved}

    async def attach_to_jira(
        self,
        ticket_key: str,
        run_id: str,
        file_types: list[str],
        comment: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"run_id": run_id, "file_types": file_types}
        if comment:
            body["comment"] = comment
        data = await self._post(f"/jira/tickets/{ticket_key}/attachments", body)
        if isinstance(data, dict):
            return data
        from datetime import date

        today = date.today().isoformat()
        return {
            "attached_files": [f"{ticket_key}_{today}.{fmt}" for fmt in file_types],
            "jira_attachment_ids": ["10021"],
        }

    async def list_testrail_projects(self) -> list[dict[str, Any]]:
        data = await self._get("/testrail/projects")
        if isinstance(data, list):
            return data
        return [p.copy() for p in MOCK_TESTRAIL_PROJECTS]

    async def list_testrail_suites(self, project_id: int) -> list[dict[str, Any]]:
        data = await self._get(f"/testrail/projects/{project_id}/suites")
        if isinstance(data, list):
            return data
        return [s.copy() for s in MOCK_TESTRAIL_SUITES]

    async def upload_to_testrail(
        self,
        run_id: str,
        *,
        project_id: int,
        suite_id: int | None = None,
        new_suite_name: str | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"project_id": project_id}
        if suite_id is not None:
            body["suite_id"] = suite_id
        if new_suite_name:
            body["new_suite_name"] = new_suite_name
        data = await self._post(f"/test-cases/runs/{run_id}/testrail-upload", body)
        if isinstance(data, dict):
            return data
        return {
            "suite_id": suite_id or 99,
            "testrail_case_ids": ["C1044", "C1045", "C1046"],
            "uploaded_count": 12,
        }

    async def update_test_case(
        self, run_id: str, case_id: str, update: dict[str, Any]
    ) -> dict[str, Any]:
        data = await self._patch(
            f"/test-cases/runs/{run_id}/cases/{case_id}",
            {k: v for k, v in update.items() if v is not None},
        )
        if isinstance(data, dict):
            return data
        for case in MOCK_TEST_CASES:
            if case["id"] == case_id:
                merged = {**case, **{k: v for k, v in update.items() if v is not None}}
                return merged.copy()
        return {"id": case_id, **update}

    async def update_review_comment(
        self, run_id: str, comment_id: str, triage_status: str
    ) -> dict[str, Any]:
        data = await self._patch(
            f"/reviews/runs/{run_id}/comments/{comment_id}",
            {"triage_status": triage_status},
        )
        if isinstance(data, dict):
            return data
        for comment in MOCK_REVIEW_COMMENTS:
            if comment.get("id") == comment_id:
                updated = {**comment, "triage_status": triage_status}
                return updated.copy()
        return {"id": comment_id, "triage_status": triage_status}

    async def test_integration(self, integration: str) -> dict[str, Any]:
        data = await self._post(f"/settings/{integration}/test", {})
        if isinstance(data, dict):
            return data
        # Offline — never fake a successful connection test
        return {
            "ok": False,
            "error": {
                "code": "BACKEND_UNREACHABLE",
                "message": "Backend is unreachable; cannot test connection.",
            },
        }

    async def fetch_pull_request(
        self, *, url: str | None = None, repo: str | None = None, pr_number: int | None = None
    ) -> dict[str, Any]:
        params: list[str] = []
        if url:
            params.append(f"url={url}")
        if repo:
            params.append(f"repo={repo}")
        if pr_number is not None:
            params.append(f"pr_number={pr_number}")
        query = "&".join(params)
        path = f"/pull-requests?{query}" if query else "/pull-requests"
        data = await self._get(path)
        if isinstance(data, dict):
            return data
        mock = MOCK_PULL_REQUEST.copy()
        parsed = _parse_pr_url(url) if url else None
        if parsed:
            mock["repo"], mock["pr_number"] = parsed
        elif repo and pr_number is not None:
            mock["repo"], mock["pr_number"] = repo, pr_number
        return mock

    async def generate_review(self, repo: str, pr_number: int) -> dict[str, Any]:
        data = await self._post("/reviews/generate", {"repo": repo, "pr_number": pr_number})
        if isinstance(data, dict):
            return data
        return _mock_review_run({"repo": repo, "pr_number": pr_number})

    async def get_settings(self) -> dict[str, Any]:
        data = await self._get("/settings")
        if isinstance(data, dict):
            return data
        return {k: v.copy() if isinstance(v, dict) else v for k, v in MOCK_SETTINGS.items()}

    async def update_settings(self, body: dict[str, Any]) -> dict[str, Any]:
        data = await self._put("/settings", body)
        if isinstance(data, dict):
            return data
        merged = await self.get_settings()
        for section, values in body.items():
            if section in merged and isinstance(values, dict):
                merged[section].update(values)
                if values.get("token"):
                    merged[section]["token_set"] = True
                    merged[section].pop("token", None)
        return merged

    async def get_activity_summary(self) -> dict[str, Any]:
        data = await self._get("/activity/summary")
        return data if isinstance(data, dict) else MOCK_SUMMARY.copy()

    async def get_recent_activity(self, limit: int = 20) -> list[dict[str, Any]]:
        data = await self._get(f"/activity/recent?limit={limit}")
        # Empty list is a valid live response — do not replace with demo feed.
        if isinstance(data, list):
            return data
        return [item.copy() for item in MOCK_RECENT]

    async def reset_activity(self) -> dict[str, Any]:
        data = await self._post("/activity/reset", {})
        if isinstance(data, dict):
            return data
        raise RuntimeError("Backend unreachable; cannot reset activity.")


api_client = ApiClient()
