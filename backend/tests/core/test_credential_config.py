"""Startup checks for integration-token encryption key."""

import pytest
from cryptography.fernet import Fernet

from app.core.credential_config import (
    credentials_encryption_key_is_missing,
    ensure_credentials_encryption_key,
)


def test_missing_key_detected():
    assert credentials_encryption_key_is_missing("")
    assert credentials_encryption_key_is_missing("not-a-fernet-key")


def test_ensure_key_fails_closed_without_debug(monkeypatch):
    monkeypatch.setattr("app.config.settings.debug", False)
    monkeypatch.setattr("app.config.settings.credentials_encryption_key", "")
    with pytest.raises(RuntimeError, match="CREDENTIALS_ENCRYPTION_KEY"):
        ensure_credentials_encryption_key()


def test_ensure_key_ephemeral_when_debug(monkeypatch):
    monkeypatch.setattr("app.config.settings.debug", True)
    monkeypatch.setattr("app.config.settings.credentials_encryption_key", "")
    ensure_credentials_encryption_key()
    from app.config import settings

    assert not credentials_encryption_key_is_missing(settings.credentials_encryption_key)
    Fernet(settings.credentials_encryption_key.encode("utf-8"))
