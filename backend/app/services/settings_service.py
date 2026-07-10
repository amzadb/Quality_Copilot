"""Settings persistence and integration connection tests."""

from fastapi import Depends

from app.core.errors import not_implemented_yet
from app.integrations.git_provider import GitProviderIntegration, get_git_provider_integration
from app.integrations.jira import JiraIntegration, get_jira_integration
from app.integrations.llm import LLMIntegration, get_llm_integration
from app.integrations.testrail import TestRailIntegration, get_testrail_integration
from app.schemas.common import ConnectionTestResponse
from app.schemas.settings import SettingsResponse, SettingsUpdate


class SettingsService:
    def __init__(
        self,
        jira: JiraIntegration,
        git: GitProviderIntegration,
        testrail: TestRailIntegration,
        llm: LLMIntegration,
    ) -> None:
        self._integrations = {
            "jira": jira,
            "git_provider": git,
            "testrail": testrail,
            "llm": llm,
        }

    async def get_settings(self) -> SettingsResponse:
        not_implemented_yet(
            "Settings retrieval",
            "Integration settings storage is not implemented yet.",
        )

    async def update_settings(self, update: SettingsUpdate) -> SettingsResponse:
        not_implemented_yet(
            "Settings update",
            "Updating integration settings is not implemented yet.",
        )

    async def test_connection(self, integration: str) -> ConnectionTestResponse:
        client = self._integrations.get(integration)
        if client is None:
            not_implemented_yet(
                "Connection test",
                f"Unknown integration '{integration}'.",
            )
        return await client.test_connection()


def get_settings_service(
    jira: JiraIntegration = Depends(get_jira_integration),
    git: GitProviderIntegration = Depends(get_git_provider_integration),
    testrail: TestRailIntegration = Depends(get_testrail_integration),
    llm: LLMIntegration = Depends(get_llm_integration),
) -> SettingsService:
    return SettingsService(jira, git, testrail, llm)
