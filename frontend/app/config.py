from pydantic_settings import BaseSettings, SettingsConfigDict


class FrontendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_title: str = "Quality Copilot"
    backend_url: str = "http://127.0.0.1:8000"
    api_v1_prefix: str = "/api/v1"
    port: int = 9000
    reload: bool = True
    # Required by NiceGUI for app.storage.user (browser session storage)
    storage_secret: str = "dev-only-change-me-quality-copilot-frontend"

    @property
    def api_base(self) -> str:
        return f"{self.backend_url.rstrip('/')}{self.api_v1_prefix}"


settings = FrontendSettings()
