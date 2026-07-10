from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Quality Copilot"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False


settings = AppSettings()
