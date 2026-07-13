"""Tests for Git provider integration."""

from unittest.mock import AsyncMock, patch

import pytest

from app.core.errors import AppError
from app.integrations.git_provider import GitProviderIntegration
from tests.conftest import run_async


def test_fetch_pull_request_success(configured_credentials):
    integration = GitProviderIntegration(configured_credentials)

    with (
        patch("app.integrations.git_provider.request_json", new_callable=AsyncMock) as mock_request,
        patch.object(integration, "_fetch_bitbucket_diff", new_callable=AsyncMock) as mock_diff,
    ):
        mock_request.return_value = {"title": "Refactor payment retry logic"}
        mock_diff.return_value = "diff --git a/file.py b/file.py\n+added\n-removed\n"
        pr = run_async(
            integration.fetch_pull_request(url="bitbucket.org/acme/payments/pull-requests/318")
        )

    assert pr.provider == "bitbucket"
    assert pr.repo == "acme/payments"
    assert pr.pr_number == 318
    assert pr.title == "Refactor payment retry logic"
    assert pr.files_changed == 1
    assert pr.additions >= 1
    assert pr.deletions >= 1


def test_fetch_pull_request_not_found(configured_credentials):
    integration = GitProviderIntegration(configured_credentials)

    with patch("app.integrations.git_provider.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = AppError(status_code=404, code="NOT_FOUND", message="missing")
        with pytest.raises(AppError) as exc:
            run_async(integration.fetch_pull_request(repo="acme/payments", pr_number=999))

    assert exc.value.code == "PR_NOT_FOUND"


def test_test_connection_success(configured_credentials):
    integration = GitProviderIntegration(configured_credentials)

    with patch("app.integrations.git_provider.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"username": "qa-bot"}
        result = run_async(integration.test_connection())

    assert result.ok is True


def test_test_connection_auth_failed(configured_credentials):
    integration = GitProviderIntegration(configured_credentials)

    with patch("app.integrations.git_provider.request_json", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = AppError(status_code=401, code="AUTH_FAILED", message="bad token")
        result = run_async(integration.test_connection())

    assert result.ok is False
    assert result.error.code == "GIT_AUTH_FAILED"
