"""Tests for JIRA integration."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.errors import AppError
from app.integrations.jira import JiraIntegration, _parse_ticket_payload
from app.schemas.jira import JiraAttachmentRequest
from tests.conftest import run_async


def test_fetch_ticket_success(configured_credentials):
    integration = JiraIntegration(configured_credentials)
    issue_payload = {
        "key": "PROJ-1042",
        "fields": {
            "summary": "Add SSO login flow",
            "description": {
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Users authenticate via SSO."}],
                    }
                ],
            },
            "issuetype": {"name": "Story"},
        },
    }

    with patch("app.integrations.jira.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = issue_payload
        ticket = run_async(integration.fetch_ticket("proj-1042"))

    assert ticket.key == "PROJ-1042"
    assert ticket.title == "Add SSO login flow"
    assert "SSO" in ticket.description
    assert ticket.issue_type == "Story"


def test_fetch_ticket_not_found(configured_credentials):
    integration = JiraIntegration(configured_credentials)

    with patch("app.integrations.jira.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = AppError(status_code=404, code="NOT_FOUND", message="missing")
        with pytest.raises(AppError) as exc:
            run_async(integration.fetch_ticket("PROJ-9999"))

    assert exc.value.code == "JIRA_NOT_FOUND"


def test_fetch_ticket_auth_failed(configured_credentials):
    integration = JiraIntegration(configured_credentials)

    with patch("app.integrations.jira.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = AppError(status_code=401, code="AUTH_FAILED", message="bad auth")
        with pytest.raises(AppError) as exc:
            run_async(integration.fetch_ticket("PROJ-1042"))

    assert exc.value.code == "JIRA_AUTH_FAILED"


def test_test_connection_success(configured_credentials):
    integration = JiraIntegration(configured_credentials)

    with patch("app.integrations.jira.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"accountId": "abc"}
        result = run_async(integration.test_connection())

    assert result.ok is True


def test_test_connection_not_configured(credentials_file):
    integration = JiraIntegration(credentials_file)
    result = run_async(integration.test_connection())
    assert result.ok is False
    assert result.error.code == "JIRA_NOT_CONFIGURED"


def test_attach_files_posts_comment_and_files(configured_credentials):
    integration = JiraIntegration(configured_credentials)
    body = JiraAttachmentRequest(
        run_id="run-1",
        file_types=["docx"],
        comment="Attaching generated test cases.",
    )

    with (
        patch("app.integrations.jira.request_json", new_callable=AsyncMock) as mock_request,
        patch.object(integration, "attach_file", new_callable=AsyncMock) as mock_attach,
    ):
        mock_attach.return_value = "10021"
        response = run_async(
            integration.attach_files(
                "PROJ-1042",
                body,
                files=[("PROJ-1042.docx", b"docx-bytes")],
            )
        )

    mock_request.assert_awaited_once()
    mock_attach.assert_awaited_once()
    assert response.attached_files == ["PROJ-1042.docx"]
    assert response.jira_attachment_ids == ["10021"]


def test_parse_ticket_payload_plain_description():
    payload = {
        "key": "PROJ-1",
        "fields": {
            "summary": "Title",
            "description": "Plain text description",
            "issuetype": {"name": "Bug"},
        },
    }
    ticket = _parse_ticket_payload("PROJ-1", payload, "https://acme.atlassian.net")
    assert ticket.description == "Plain text description"
    assert ticket.url.endswith("/browse/PROJ-1")
