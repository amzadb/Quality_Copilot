from pydantic import BaseModel, Field

from app.schemas.common import GitProviderType, LLMProvider


class JiraSettings(BaseModel):
    base_url: str | None = None
    token: str | None = Field(default=None, description="Write-only; never returned on GET")
    token_set: bool = False


class GitProviderSettings(BaseModel):
    type: GitProviderType | None = None
    workspace: str | None = None
    token: str | None = Field(default=None, description="Write-only; never returned on GET")
    token_set: bool = False


class TestRailSettings(BaseModel):
    base_url: str | None = None
    username: str | None = None
    token: str | None = Field(default=None, description="Write-only; never returned on GET")
    token_set: bool = False


class LLMSettings(BaseModel):
    provider: LLMProvider | None = None
    token: str | None = Field(default=None, description="Write-only; never returned on GET")
    token_set: bool = False


class SettingsResponse(BaseModel):
    jira: JiraSettings
    git_provider: GitProviderSettings
    testrail: TestRailSettings
    llm: LLMSettings


class SettingsUpdate(BaseModel):
    jira: JiraSettings | None = None
    git_provider: GitProviderSettings | None = None
    testrail: TestRailSettings | None = None
    llm: LLMSettings | None = None
