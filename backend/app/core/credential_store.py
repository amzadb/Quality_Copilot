"""Server-side integration credential storage with masked reads."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.config import settings
from app.schemas.settings import (
    GitProviderSettings,
    JiraSettings,
    LLMSettings,
    SettingsResponse,
    SettingsUpdate,
    TestRailSettings,
)


def _empty_store() -> dict[str, dict[str, Any]]:
    return {
        "jira": {},
        "git_provider": {},
        "testrail": {},
        "llm": {},
    }


class CredentialStore:
    """Persists integration secrets to a JSON file on disk."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(settings.credentials_path)
        self._data: dict[str, dict[str, Any]] | None = None

    def _ensure_loaded(self) -> dict[str, dict[str, Any]]:
        if self._data is not None:
            return self._data

        if self._path.exists():
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._data = {**_empty_store(), **raw}
        else:
            self._data = _empty_store()
        return self._data

    def reload(self) -> None:
        self._data = None
        self._ensure_loaded()

    def _save(self) -> None:
        data = self._ensure_loaded()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def get_section(self, name: str) -> dict[str, Any]:
        return deepcopy(self._ensure_loaded().get(name, {}))

    def merge_update(self, update: SettingsUpdate) -> SettingsResponse:
        data = self._ensure_loaded()
        payload = update.model_dump(exclude_none=True)

        for section, values in payload.items():
            if section not in data:
                continue
            section_values = {k: v for k, v in values.items() if v is not None}
            if "token" in section_values and section_values["token"]:
                data[section]["token"] = section_values.pop("token")
            data[section].update(section_values)

        self._save()
        return self.to_response()

    def to_response(self) -> SettingsResponse:
        data = self._ensure_loaded()
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


_store: CredentialStore | None = None


def get_credential_store() -> CredentialStore:
    global _store
    if _store is None:
        _store = CredentialStore()
    return _store


def reset_credential_store(path: Path | None = None) -> CredentialStore:
    """Replace the process-wide store — used in tests."""
    global _store
    _store = CredentialStore(path)
    return _store
