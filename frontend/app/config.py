import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class FrontendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_title: str = "Quality Copilot"
    backend_url: str = "http://127.0.0.1:8000"
    api_v1_prefix: str = "/api/v1"
    host: str = "127.0.0.1"
    port: int = 9000
    reload: bool = True
    # Required by NiceGUI for app.storage.user (browser session storage)
    storage_secret: str = "dev-only-change-me-quality-copilot-frontend"

    @property
    def api_base(self) -> str:
        return f"{self.backend_url.rstrip('/')}{self.api_v1_prefix}"


def _port_from_env(default: int = 9000) -> int:
    raw = os.environ.get("PORT")
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


settings = FrontendSettings()
# Render and similar platforms inject PORT; prefer it when present.
if os.environ.get("PORT"):
    settings.port = _port_from_env(settings.port)
if os.environ.get("RENDER"):
    settings.host = "0.0.0.0"
    settings.reload = False
