"""Startup auth secret hardening."""

import pytest

from app.core.auth_config import ensure_auth_secrets, jwt_secret_is_insecure


def test_known_default_jwt_secret_is_insecure():
    assert jwt_secret_is_insecure("dev-only-change-me-quality-copilot")
    assert jwt_secret_is_insecure("")
    assert jwt_secret_is_insecure("short")
    assert not jwt_secret_is_insecure("a-sufficiently-long-unique-secret")


def test_ensure_auth_secrets_fails_closed_without_debug(monkeypatch):
    monkeypatch.setattr("app.config.settings.debug", False)
    monkeypatch.setattr("app.config.settings.jwt_secret", "")
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        ensure_auth_secrets()


def test_ensure_auth_secrets_rejects_public_default_without_debug(monkeypatch):
    monkeypatch.setattr("app.config.settings.debug", False)
    monkeypatch.setattr(
        "app.config.settings.jwt_secret",
        "dev-only-change-me-quality-copilot",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        ensure_auth_secrets()


def test_ensure_auth_secrets_ephemeral_when_debug(monkeypatch):
    monkeypatch.setattr("app.config.settings.debug", True)
    monkeypatch.setattr("app.config.settings.jwt_secret", "")
    ensure_auth_secrets()
    from app.config import settings

    assert not jwt_secret_is_insecure(settings.jwt_secret)
