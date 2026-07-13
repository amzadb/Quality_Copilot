"""Tests for credential store module."""

from app.core.credential_store import CredentialStore
from app.schemas.settings import JiraSettings, SettingsUpdate


def test_persist_and_reload(tmp_path):
    path = tmp_path / "credentials.json"
    store = CredentialStore(path)
    store.merge_update(
        SettingsUpdate(jira=JiraSettings(base_url="acme.atlassian.net", token="secret"))
    )

    reloaded = CredentialStore(path)
    section = reloaded.get_section("jira")
    assert section["base_url"] == "acme.atlassian.net"
    assert section["token"] == "secret"
