"""TestRail API integration — suites, test cases, case IDs."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import Depends

from app.core.credential_store import CredentialStore, get_credential_store
from app.core.errors import AppError
from app.integrations._http import connection_failed, connection_ok, normalize_base_url, request_json
from app.schemas.common import ConnectionTestResponse
from app.schemas.test_cases import TestCase
from app.schemas.testrail import (
    TestRailProject,
    TestRailSuite,
    TestRailUploadRequest,
    TestRailUploadResponse,
)


class TestRailIntegration:
    def __init__(self, credentials: CredentialStore) -> None:
        self._credentials = credentials

    def _config(self) -> tuple[str, tuple[str, str]]:
        section = self._credentials.get_section("testrail")
        base_url = section.get("base_url")
        username = section.get("username")
        token = section.get("token")
        if not base_url or not username or not token:
            raise AppError(
                status_code=400,
                code="TESTRAIL_NOT_CONFIGURED",
                message="TestRail is not configured. Set base URL, username, and API key in Settings.",
            )
        normalized = normalize_base_url(base_url)
        api_root = f"{normalized}/index.php?/api/v2"
        return api_root, (username, token)

    async def list_projects(self) -> list[TestRailProject]:
        api_root, auth = self._config()
        payload = await request_json("GET", f"{api_root}/get_projects", auth=auth)
        projects = payload.get("projects") if isinstance(payload, dict) else payload
        if not isinstance(projects, list):
            return []
        return [TestRailProject(id=item["id"], name=item["name"]) for item in projects]

    async def list_suites(self, project_id: int) -> list[TestRailSuite]:
        api_root, auth = self._config()
        payload = await request_json("GET", f"{api_root}/get_suites/{project_id}", auth=auth)
        if not isinstance(payload, list):
            return []
        return [TestRailSuite(id=item["id"], name=item["name"]) for item in payload]

    async def find_or_create_suite(
        self, project_id: int, suite_id: int | None, new_suite_name: str | None
    ) -> int:
        if suite_id is not None:
            return suite_id
        if not new_suite_name:
            raise AppError(
                status_code=400,
                code="TESTRAIL_SUITE_REQUIRED",
                message="Provide either suite_id or new_suite_name for TestRail upload.",
            )

        api_root, auth = self._config()
        payload = await request_json(
            "POST",
            f"{api_root}/add_suite/{project_id}",
            auth=auth,
            json={"name": new_suite_name},
        )
        return int(payload["id"])

    async def add_test_cases(self, suite_id: int, cases: list[TestCase]) -> list[str]:
        api_root, auth = self._config()
        case_ids: list[str] = []

        for case in cases:
            body = self._case_payload(case)
            payload = await request_json(
                "POST",
                f"{api_root}/add_case/{suite_id}",
                auth=auth,
                json=body,
            )
            case_ids.append(f"C{payload['id']}")

        return case_ids

    @staticmethod
    def _case_payload(case: TestCase) -> dict[str, Any]:
        steps = [{"content": step, "expected": case.expected_result} for step in case.steps]
        if not steps:
            steps = [{"content": case.title, "expected": case.expected_result}]
        return {
            "title": case.title,
            "type_id": 1,
            "custom_steps_separated": steps,
        }

    async def upload_run(
        self, cases: list[TestCase], request: TestRailUploadRequest
    ) -> TestRailUploadResponse:
        suite_id = await self.find_or_create_suite(
            request.project_id,
            request.suite_id,
            request.new_suite_name,
        )
        case_ids = await self.add_test_cases(suite_id, cases)
        return TestRailUploadResponse(
            suite_id=suite_id,
            testrail_case_ids=case_ids,
            uploaded_count=len(case_ids),
        )

    async def test_connection(self) -> ConnectionTestResponse:
        try:
            api_root, auth = self._config()
        except AppError as exc:
            return connection_failed(exc.code, str(exc.detail))

        try:
            await request_json("GET", f"{api_root}/get_projects", auth=auth)
        except AppError as exc:
            if exc.code == "AUTH_FAILED":
                return connection_failed("TESTRAIL_AUTH_FAILED", "TestRail authentication failed.")
            return connection_failed("TESTRAIL_CONNECTION_FAILED", str(exc.detail))
        except httpx.HTTPError as exc:
            return connection_failed("TESTRAIL_CONNECTION_FAILED", str(exc))

        return connection_ok()


def get_testrail_integration(
    credentials: CredentialStore = Depends(get_credential_store),
) -> TestRailIntegration:
    return TestRailIntegration(credentials)
