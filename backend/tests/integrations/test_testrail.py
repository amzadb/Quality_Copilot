"""Tests for TestRail integration."""

from unittest.mock import AsyncMock, patch

from app.core.errors import AppError
from app.integrations.testrail import TestRailIntegration
from app.schemas.test_cases import TestCase
from app.schemas.testrail import TestRailUploadRequest
from tests.conftest import run_async


def test_list_projects_success(configured_credentials):
    integration = TestRailIntegration(configured_credentials)

    with patch("app.integrations.testrail.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {
            "projects": [
                {"id": 1, "name": "Payments platform"},
                {"id": 2, "name": "Core platform"},
            ]
        }
        projects = run_async(integration.list_projects())

    assert len(projects) == 2
    assert projects[0].name == "Payments platform"


def test_list_suites_success(configured_credentials):
    integration = TestRailIntegration(configured_credentials)

    with patch("app.integrations.testrail.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = [
            {"id": 12, "name": "Login and authentication"},
        ]
        suites = run_async(integration.list_suites(1))

    assert len(suites) == 1
    assert suites[0].id == 12


def test_upload_run_existing_suite(configured_credentials):
    integration = TestRailIntegration(configured_credentials)
    cases = [
        TestCase(
            id="TC-01",
            title="SSO login succeeds",
            type="functional",
            steps=["Open login"],
            expected_result="Dashboard loads.",
        )
    ]
    request = TestRailUploadRequest(project_id=1, suite_id=12)

    with patch("app.integrations.testrail.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"id": 1044}
        response = run_async(integration.upload_run(cases, request))

    assert response.suite_id == 12
    assert response.uploaded_count == 1
    assert response.testrail_case_ids == ["C1044"]


def test_test_connection_auth_failed(configured_credentials):
    integration = TestRailIntegration(configured_credentials)

    with patch("app.integrations.testrail.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = AppError(status_code=401, code="AUTH_FAILED", message="bad key")
        result = run_async(integration.test_connection())

    assert result.ok is False
    assert result.error.code == "TESTRAIL_AUTH_FAILED"
