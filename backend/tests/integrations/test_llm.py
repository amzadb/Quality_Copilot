"""Tests for LLM integration."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.core.errors import AppError
from app.integrations.llm import LLMIntegration
from app.schemas.jira import JiraTicketResponse
from app.schemas.pull_requests import PullRequestResponse
from tests.conftest import run_async


def test_generate_test_cases_success(configured_credentials):
    integration = LLMIntegration(configured_credentials)
    ticket = JiraTicketResponse(
        key="PROJ-1042",
        title="Add SSO login flow",
        description="Users authenticate via SSO.",
        issue_type="Story",
        url="https://acme.atlassian.net/browse/PROJ-1042",
    )
    llm_payload = {
        "test_cases": [
            {
                "id": "TC-01",
                "title": "SSO login succeeds",
                "type": "functional",
                "steps": ["Open login", "Click SSO"],
                "expected_result": "User reaches dashboard.",
            }
        ]
    }

    with patch("app.integrations.llm.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {
            "content": [{"type": "text", "text": json.dumps(llm_payload)}]
        }
        output = run_async(integration.generate_test_cases(ticket))

    assert len(output.test_cases) == 1
    assert output.test_cases[0].id == "TC-01"


def test_generate_test_cases_parse_failure(configured_credentials):
    integration = LLMIntegration(configured_credentials)
    ticket = JiraTicketResponse(
        key="PROJ-1042",
        title="Title",
        description="Description",
        issue_type="Story",
        url="https://acme.atlassian.net/browse/PROJ-1042",
    )

    with patch("app.integrations.llm.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"content": [{"type": "text", "text": "not-json"}]}
        with pytest.raises(AppError) as exc:
            run_async(integration.generate_test_cases(ticket))

    assert exc.value.code == "LLM_PARSE_FAILED"


def test_generate_review_success(configured_credentials):
    integration = LLMIntegration(configured_credentials)
    pull_request = PullRequestResponse(
        provider="bitbucket",
        repo="acme/payments",
        pr_number=318,
        title="Refactor payment retry logic",
        files_changed=2,
        additions=10,
        deletions=3,
        diff="diff --git a/retry.py b/retry.py",
    )
    llm_payload = {
        "comments": [
            {
                "file": "retry.py",
                "line": 42,
                "severity": "high",
                "comment": "Retry count is not reset.",
            }
        ]
    }

    with patch("app.integrations.llm.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {
            "content": [{"type": "text", "text": json.dumps(llm_payload)}]
        }
        output = run_async(integration.generate_review(pull_request))

    assert len(output.comments) == 1
    assert output.comments[0].severity == "high"


def test_test_connection_success(configured_credentials):
    integration = LLMIntegration(configured_credentials)

    with patch("app.integrations.llm.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"content": [{"type": "text", "text": "OK"}]}
        result = run_async(integration.test_connection())

    assert result.ok is True


def test_test_connection_not_configured(credentials_file):
    integration = LLMIntegration(credentials_file)
    result = run_async(integration.test_connection())
    assert result.ok is False
    assert result.error.code == "LLM_NOT_CONFIGURED"
