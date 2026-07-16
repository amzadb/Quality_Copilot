"""Integration credential storage — per-user DB or legacy JSON file fallback."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.core.credential_encryption import decrypt_sections, encrypt_sections
from app.core.deps import get_optional_user
from app.models.base import get_db
from app.models.user import User, UserSettings
from app.schemas.settings import (
    GitProviderSettings,
    JiraSettings,
    LLMSettings,
    SettingsResponse,
    SettingsUpdate,
    TestRailSettings,
)

SECTION_NAMES = ("jira", "git_provider", "testrail", "llm")


def _empty_sections() -> dict[str, dict[str, Any]]:
    return {name: {} for name in SECTION_NAMES}


def _to_response(data: dict[str, dict[str, Any]]) -> SettingsResponse:
    return SettingsResponse(
        jira=JiraSettings(
            base_url=data["jira"].get("base_url"),
            token_set=bool(data["jira"].get("token")),
        ),
        git_provider=GitProviderSettings(
            type=data["git_provider"].get("type"),
            workspace=data["git_provider"].get("workspace"),
            username=data["git_provider"].get("username"),
            token_set=bool(data["git_provider"].get("token")),
        ),
        testrail=TestRailSettings(
            base_url=data["testrail"].get("base_url"),
            username=data["testrail"].get("username"),
            token_set=bool(data["testrail"].get("token")),
        ),
        llm=LLMSettings(
            provider=data["llm"].get("provider"),
            token_set=bool(data["llm"].get("token")),
        ),
    )


def _apply_update(data: dict[str, dict[str, Any]], update: SettingsUpdate) -> dict[str, dict[str, Any]]:
    result = {name: dict(data.get(name) or {}) for name in SECTION_NAMES}
    for section_name in SECTION_NAMES:
        section_model = getattr(update, section_name)
        if section_model is None:
            continue
        section_values = section_model.model_dump(exclude_none=True)
        token = getattr(section_model, "token", None)
        if token:
            result[section_name]["token"] = token
        result[section_name].update(section_values)
    return result


class FileCredentialStore:
    """Legacy shared JSON credentials file (unauthenticated / fallback)."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(settings.credentials_path)
        self._data: dict[str, dict[str, Any]] | None = None

    def _ensure_loaded(self) -> dict[str, dict[str, Any]]:
        if self._data is not None:
            return self._data
        if self._path.exists():
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            merged = {**_empty_sections(), **raw}
            self._data = decrypt_sections(merged)
        else:
            self._data = _empty_sections()
        return self._data

    def reload(self) -> None:
        self._data = None
        self._ensure_loaded()

    def _save(self) -> None:
        data = self._ensure_loaded()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        encrypted = encrypt_sections(data)
        self._path.write_text(json.dumps(encrypted, indent=2), encoding="utf-8")

    def get_section(self, name: str) -> dict[str, Any]:
        return deepcopy(self._ensure_loaded().get(name, {}))

    def merge_update(self, update: SettingsUpdate) -> SettingsResponse:
        data = self._ensure_loaded()
        merged = _apply_update(data, update)
        self._data = merged
        self._save()
        return _to_response(merged)

    def to_response(self) -> SettingsResponse:
        return _to_response(self._ensure_loaded())


class DbCredentialStore:
    """Per-user integration settings persisted in user_settings."""

    def __init__(self, db: Session, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def _row(self) -> UserSettings:
        row = self._db.get(UserSettings, self._user_id)
        if row is None:
            row = UserSettings(
                user_id=self._user_id,
                jira={},
                git_provider={},
                testrail={},
                llm={},
            )
            self._db.add(row)
            self._db.commit()
            self._db.refresh(row)
        return row

    def _as_dict(self, row: UserSettings) -> dict[str, dict[str, Any]]:
        stored = {
            "jira": dict(row.jira or {}),
            "git_provider": dict(row.git_provider or {}),
            "testrail": dict(row.testrail or {}),
            "llm": dict(row.llm or {}),
        }
        return decrypt_sections(stored)

    def get_section(self, name: str) -> dict[str, Any]:
        return deepcopy(self._as_dict(self._row()).get(name, {}))

    def merge_update(self, update: SettingsUpdate) -> SettingsResponse:
        row = self._row()
        merged = _apply_update(self._as_dict(row), update)
        encrypted = encrypt_sections(merged)
        row.jira = encrypted["jira"]
        row.git_provider = encrypted["git_provider"]
        row.testrail = encrypted["testrail"]
        row.llm = encrypted["llm"]
        self._db.commit()
        self._db.refresh(row)
        return _to_response(merged)

    def to_response(self) -> SettingsResponse:
        return _to_response(self._as_dict(self._row()))


# Backward-compatible alias used by tests and docs.
CredentialStore = FileCredentialStore

_file_store: FileCredentialStore | None = None


def reset_credential_store(path: Path | None = None) -> FileCredentialStore:
    """Replace the process-wide file store — used in tests."""
    global _file_store
    _file_store = FileCredentialStore(path)
    return _file_store


def get_file_credential_store() -> FileCredentialStore:
    global _file_store
    if _file_store is None:
        _file_store = FileCredentialStore()
    return _file_store


def get_credential_store(
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> FileCredentialStore | DbCredentialStore:
    """Authenticated users get DB settings; otherwise legacy file fallback."""
    if user is not None:
        return DbCredentialStore(db, user.id)
    return get_file_credential_store()
