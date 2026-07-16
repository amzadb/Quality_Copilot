"""Encrypt integration API tokens at rest (DB + legacy credentials file)."""

from __future__ import annotations

from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

ENCRYPTED_PREFIX = "enc:v1:"
TOKEN_FIELD = "token"
SECTION_NAMES = ("jira", "git_provider", "testrail", "llm")


def is_encrypted_token(value: str) -> bool:
    return isinstance(value, str) and value.startswith(ENCRYPTED_PREFIX)


def _fernet() -> Fernet:
    key = (settings.credentials_encryption_key or "").strip()
    if not key:
        raise RuntimeError(
            "CREDENTIALS_ENCRYPTION_KEY is not configured. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode("utf-8"))


def encrypt_token(plaintext: str) -> str:
    """Return Fernet ciphertext prefixed for storage. Empty strings pass through."""
    if not plaintext:
        return plaintext
    if is_encrypted_token(plaintext):
        return plaintext
    token = _fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTED_PREFIX}{token}"


def decrypt_token(stored: str) -> str:
    """Decrypt a stored token; legacy plaintext values are returned unchanged."""
    if not stored:
        return stored
    if not is_encrypted_token(stored):
        return stored
    ciphertext = stored[len(ENCRYPTED_PREFIX) :]
    try:
        return _fernet().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Failed to decrypt stored credential token (wrong encryption key?)") from exc


def encrypt_section(section: dict[str, Any]) -> dict[str, Any]:
    result = dict(section)
    token = result.get(TOKEN_FIELD)
    if isinstance(token, str) and token:
        result[TOKEN_FIELD] = encrypt_token(token)
    return result


def decrypt_section(section: dict[str, Any]) -> dict[str, Any]:
    result = dict(section)
    token = result.get(TOKEN_FIELD)
    if isinstance(token, str) and token:
        result[TOKEN_FIELD] = decrypt_token(token)
    return result


def encrypt_sections(data: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {name: encrypt_section(dict(data.get(name) or {})) for name in SECTION_NAMES}


def decrypt_sections(data: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {name: decrypt_section(dict(data.get(name) or {})) for name in SECTION_NAMES}
