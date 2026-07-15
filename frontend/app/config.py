import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_backend_url(url: str) -> str:
    """Ensure BACKEND_URL is an absolute http(s) URL (Render may inject host only)."""
    value = (url or "").strip().rstrip("/")
    if not value:
        return "http://127.0.0.1:8000"
    if value.startswith("http://") or value.startswith("https://"):
        return value
    # Blueprint fromService `host` yields e.g. quality-copilot-api.onrender.com
    return f"https://{value}"


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

    @field_validator("backend_url", mode="before")
    @classmethod
    def _normalize_backend_url(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_backend_url(value)
        return value

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


def _apply_runtime_overrides(cfg: FrontendSettings) -> FrontendSettings:
    """Prefer PLATFORM-injected values (Render PORT / service host)."""
    if os.environ.get("PORT"):
        cfg.port = _port_from_env(cfg.port)

    # Blueprint can set BACKEND_HOST from the API service when BACKEND_URL is unset.
    backend_host = (os.environ.get("BACKEND_HOST") or "").strip()
    backend_url_env = (os.environ.get("BACKEND_URL") or "").strip()
    if backend_host and not backend_url_env:
        cfg.backend_url = normalize_backend_url(backend_host)
    elif backend_url_env:
        cfg.backend_url = normalize_backend_url(backend_url_env)

    if os.environ.get("RENDER"):
        cfg.host = "0.0.0.0"
        cfg.reload = False
        # Local default on Render would never reach the API service.
        if "127.0.0.1" in cfg.backend_url or "localhost" in cfg.backend_url:
            print(
                "WARNING: BACKEND_URL points at localhost on Render. "
                "Set BACKEND_URL (or BACKEND_HOST) to your API service URL, "
                "e.g. https://quality-copilot-api.onrender.com"
            )
    return cfg


settings = _apply_runtime_overrides(FrontendSettings())
