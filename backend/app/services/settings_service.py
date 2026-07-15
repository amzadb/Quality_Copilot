"""Settings persistence and integration connection tests."""

from fastapi import Depends

from app.core.credential_store import DbCredentialStore, FileCredentialStore, get_credential_store
from app.core.errors import AppError
from app.integrations.git_provider import GitProviderIntegration, get_git_provider_integration
from app.integrations.jira import JiraIntegration, get_jira_integration
from app.integrations.llm import LLMIntegration, get_llm_integration
from app.integrations.testrail import TestRailIntegration, get_testrail_integration
from app.schemas.common import ConnectionTestResponse
from app.schemas.settings import SettingsResponse, SettingsUpdate

CredentialStoreLike = FileCredentialStore | DbCredentialStore


class SettingsService:
    def __init__(
        self,
        store: CredentialStoreLike,
        jira: JiraIntegration,
        git: GitProviderIntegration,
        testrail: TestRailIntegration,
        llm: LLMIntegration,
    ) -> None:
        self._store = store
        self._integrations = {
            "jira": jira,
            "git_provider": git,
            "testrail": testrail,
            "llm": llm,
        }

    async def get_settings(self) -> SettingsResponse:
        return self._store.to_response()

    async def update_settings(self, update: SettingsUpdate) -> SettingsResponse:
        return self._store.merge_update(update)

    async def test_connection(self, integration: str) -> ConnectionTestResponse:
        client = self._integrations.get(integration)
        if client is None:
            raise AppError(
                status_code=404,
                code="INTEGRATION_NOT_FOUND",
                message=f"Unknown integration '{integration}'.",
            )
        return await client.test_connection()


def get_settings_service(
    store: CredentialStoreLike = Depends(get_credential_store),
    jira: JiraIntegration = Depends(get_jira_integration),
    git: GitProviderIntegration = Depends(get_git_provider_integration),
    testrail: TestRailIntegration = Depends(get_testrail_integration),
    llm: LLMIntegration = Depends(get_llm_integration),
) -> SettingsService:
    return SettingsService(store, jira, git, testrail, llm)
