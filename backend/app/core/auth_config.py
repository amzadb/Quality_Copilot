"""Startup checks for auth secrets (JWT, optional admin seed)."""

from __future__ import annotations

import logging
import secrets

from app.config import settings

logger = logging.getLogger(__name__)

# Values that must never be used in non-debug deployments (including old example defaults).
_INSECURE_JWT_SECRETS = frozenset(
    {
        "",
        "changeme",
        "secret",
        "jwt-secret",
        # Former baked-in default (treat as compromised / public).
        "dev-only-change-me-quality-copilot",
    }
)


def jwt_secret_is_insecure(secret: str | None) -> bool:
    value = (secret or "").strip()
    return not value or value in _INSECURE_JWT_SECRETS or len(value) < 16


def ensure_auth_secrets() -> None:
    """Require a strong JWT_SECRET, or use an ephemeral one only when DEBUG=true.

    Admin seed is opt-in: ADMIN_PASSWORD must be set explicitly (no default password).
    """
    if not jwt_secret_is_insecure(settings.jwt_secret):
        return

    if settings.debug:
        settings.jwt_secret = secrets.token_urlsafe(32)
        logger.warning(
            "JWT_SECRET is missing or insecure; generated an ephemeral secret for this process. "
            "Tokens will be invalid after restart. Set JWT_SECRET in .env for stable local auth."
        )
        return

    raise RuntimeError(
        "JWT_SECRET must be set to a strong unique value (at least 16 characters). "
        "Copy backend/.env.example to .env and set JWT_SECRET "
        "(e.g. `python -c \"import secrets; print(secrets.token_urlsafe(32))\"`). "
        "For local throwaway use only, you may set DEBUG=true to allow an ephemeral secret."
    )
