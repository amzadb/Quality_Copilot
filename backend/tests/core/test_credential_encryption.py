"""Credential token encryption at rest."""

import pytest
from cryptography.fernet import Fernet

from app.config import settings
from app.core.credential_encryption import (
    ENCRYPTED_PREFIX,
    decrypt_sections,
    decrypt_token,
    encrypt_sections,
    encrypt_token,
    is_encrypted_token,
)


@pytest.fixture
def fernet_key(monkeypatch):
    key = Fernet.generate_key().decode("utf-8")
    monkeypatch.setattr(settings, "credentials_encryption_key", key)
    return key


def test_encrypt_decrypt_round_trip(fernet_key):
    encrypted = encrypt_token("secret-api-token")
    assert is_encrypted_token(encrypted)
    assert encrypted.startswith(ENCRYPTED_PREFIX)
    assert decrypt_token(encrypted) == "secret-api-token"


def test_legacy_plaintext_passes_through(fernet_key):
    assert decrypt_token("legacy-plain-token") == "legacy-plain-token"


def test_sections_encrypt_only_token_field(fernet_key):
    data = {
        "jira": {"base_url": "acme.atlassian.net", "token": "jira-secret"},
        "git_provider": {},
        "testrail": {},
        "llm": {},
    }
    encrypted = encrypt_sections(data)
    assert encrypted["jira"]["base_url"] == "acme.atlassian.net"
    assert is_encrypted_token(encrypted["jira"]["token"])
    assert decrypt_sections(encrypted)["jira"]["token"] == "jira-secret"


def test_decrypt_fails_with_wrong_key(fernet_key):
    encrypted = encrypt_token("x")
    monkeypatch_key = Fernet.generate_key().decode("utf-8")
    settings.credentials_encryption_key = monkeypatch_key
    with pytest.raises(RuntimeError, match="decrypt"):
        decrypt_token(encrypted)
