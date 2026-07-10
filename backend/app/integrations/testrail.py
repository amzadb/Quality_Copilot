"""TestRail API integration — suites, test cases, case IDs."""

from app.core.errors import not_implemented_yet
from app.schemas.common import ConnectionTestResponse
from app.schemas.test_cases import TestCase
from app.schemas.testrail import (
    TestRailProject,
    TestRailSuite,
    TestRailUploadRequest,
    TestRailUploadResponse,
)


class TestRailIntegration:
    async def list_projects(self) -> list[TestRailProject]:
        not_implemented_yet(
            "TestRail projects",
            "Listing TestRail projects is not implemented yet.",
        )

    async def list_suites(self, project_id: int) -> list[TestRailSuite]:
        not_implemented_yet(
            "TestRail suites",
            f"Listing suites for TestRail project {project_id} is not implemented yet.",
        )

    async def find_or_create_suite(
        self, project_id: int, suite_id: int | None, new_suite_name: str | None
    ) -> int:
        not_implemented_yet(
            "TestRail suite resolution",
            "Finding or creating a TestRail suite is not implemented yet.",
        )

    async def add_test_cases(
        self, suite_id: int, cases: list[TestCase]
    ) -> list[str]:
        not_implemented_yet(
            "TestRail case upload",
            f"Adding test cases to suite {suite_id} is not implemented yet.",
        )

    async def upload_run(
        self, cases: list[TestCase], request: TestRailUploadRequest
    ) -> TestRailUploadResponse:
        not_implemented_yet(
            "TestRail upload",
            "Uploading test cases to TestRail is not implemented yet.",
        )

    async def test_connection(self) -> ConnectionTestResponse:
        not_implemented_yet(
            "TestRail connection test",
            "Testing the TestRail integration is not implemented yet.",
        )


def get_testrail_integration() -> TestRailIntegration:
    return TestRailIntegration()
