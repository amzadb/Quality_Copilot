from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db_url import normalize_database_url


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
    # No default — must be set via JWT_SECRET (see ensure_auth_secrets).
    jwt_secret: str = ""
    jwt_expire_minutes: int = 60 * 24
    admin_username: str = "admin"
    # No default — admin is only seeded when ADMIN_PASSWORD is set explicitly.
    admin_password: str = ""
    # Fernet key for encrypting integration tokens at rest (see credential_encryption).
    credentials_encryption_key: str = ""

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_database_url(value)
        return value


settings = AppSettings()
