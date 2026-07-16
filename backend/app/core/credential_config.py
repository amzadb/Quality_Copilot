"""Startup checks for integration-token encryption key."""

from __future__ import annotations

import logging

from cryptography.fernet import Fernet

from app.config import settings

logger = logging.getLogger(__name__)


def credentials_encryption_key_is_missing(key: str | None) -> bool:
    value = (key or "").strip()
    if not value:
        return True
    try:
        Fernet(value.encode("utf-8"))
    except (ValueError, TypeError):
        return True
    return False


def ensure_credentials_encryption_key() -> None:
    """Require a Fernet key, or generate an ephemeral one when DEBUG=true."""
    if not credentials_encryption_key_is_missing(settings.credentials_encryption_key):
        return

    if settings.debug:
        settings.credentials_encryption_key = Fernet.generate_key().decode("utf-8")
        logger.warning(
            "CREDENTIALS_ENCRYPTION_KEY is missing or invalid; generated an ephemeral key "
            "for this process. Stored tokens will be unreadable after restart. "
            "Set CREDENTIALS_ENCRYPTION_KEY in .env for stable local dev."
        )
        return

    raise RuntimeError(
        "CREDENTIALS_ENCRYPTION_KEY must be set to a valid Fernet key. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )
