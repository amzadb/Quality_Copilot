from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Quality Copilot"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False
    database_url: str = "sqlite:///./quality_copilot.db"
    credentials_path: str = "./data/credentials.json"
    jira_email: str | None = None
    anthropic_api_version: str = "2023-06-01"
    anthropic_model: str = "claude-sonnet-5"


settings = AppSettings()
