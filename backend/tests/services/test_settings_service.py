"""Tests for credential storage and settings service."""

from app.integrations.git_provider import GitProviderIntegration
from app.integrations.jira import JiraIntegration
from app.integrations.llm import LLMIntegration
from app.integrations.testrail import TestRailIntegration
from app.schemas.settings import GitProviderSettings, JiraSettings, LLMSettings, SettingsUpdate
from app.services.settings_service import SettingsService
from tests.conftest import run_async


def test_credential_store_masks_tokens_on_read(credentials_file):
    credentials_file.merge_update(
        SettingsUpdate(
            jira=JiraSettings(base_url="acme.atlassian.net", token="secret-jira-token"),
        )
    )
    response = credentials_file.to_response()

    assert response.jira.base_url == "acme.atlassian.net"
    assert response.jira.token_set is True
    assert response.jira.token is None


def test_credential_store_partial_update_preserves_token(credentials_file):
    credentials_file.merge_update(
        SettingsUpdate(jira=JiraSettings(base_url="acme.atlassian.net", token="secret-jira-token")),
    )
    credentials_file.merge_update(
        SettingsUpdate(jira=JiraSettings(base_url="new.atlassian.net")),
    )
    stored = credentials_file.get_section("jira")

    assert stored["base_url"] == "new.atlassian.net"
    assert stored["token"] == "secret-jira-token"


def test_settings_service_get_and_update(configured_credentials):
    service = SettingsService(
        configured_credentials,
        JiraIntegration(configured_credentials),
        GitProviderIntegration(configured_credentials),
        TestRailIntegration(configured_credentials),
        LLMIntegration(configured_credentials),
    )

    current = run_async(service.get_settings())
    assert current.jira.token_set is True
    assert current.git_provider.workspace == "acme"

    updated = run_async(
        service.update_settings(
            SettingsUpdate(
                git_provider=GitProviderSettings(type="bitbucket", workspace="new-workspace"),
                llm=LLMSettings(provider="claude", token="new-llm-token"),
            )
        )
    )
    assert updated.git_provider.workspace == "new-workspace"
    assert updated.llm.token_set is True

    stored = configured_credentials.get_section("git_provider")
    assert stored["workspace"] == "new-workspace"


def test_settings_api_round_trip(app_client, auth_headers):
    response = app_client.get("/api/v1/settings", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["jira"]["token_set"] is False

    put_response = app_client.put(
        "/api/v1/settings",
        headers=auth_headers,
        json={
            "jira": {"base_url": "acme.atlassian.net", "token": "secret"},
            "llm": {"provider": "claude", "token": "llm-secret"},
        },
    )
    assert put_response.status_code == 200
    body = put_response.json()
    assert body["jira"]["token_set"] is True
    assert body["llm"]["token_set"] is True
    assert "token" not in body["jira"]
    assert "token" not in body["llm"]
