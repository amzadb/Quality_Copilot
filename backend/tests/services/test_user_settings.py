"""Per-user DB settings vs legacy file fallback."""

import json

from app.core.credential_encryption import ENCRYPTED_PREFIX, is_encrypted_token
from app.core.credential_store import DbCredentialStore, FileCredentialStore
from app.core.security import hash_password
from app.models.user import User, UserSettings
from app.schemas.settings import JiraSettings, SettingsUpdate


def test_db_settings_isolated_per_user(db_session):
    user_a = User(username="usera", password_hash=hash_password("secret12"), is_admin=False)
    user_b = User(username="userb", password_hash=hash_password("secret12"), is_admin=False)
    db_session.add_all([user_a, user_b])
    db_session.flush()
    db_session.add_all(
        [
            UserSettings(user_id=user_a.id, jira={}, git_provider={}, testrail={}, llm={}),
            UserSettings(user_id=user_b.id, jira={}, git_provider={}, testrail={}, llm={}),
        ]
    )
    db_session.commit()

    store_a = DbCredentialStore(db_session, user_a.id)
    store_b = DbCredentialStore(db_session, user_b.id)
    store_a.merge_update(
        SettingsUpdate(jira=JiraSettings(base_url="a.atlassian.net", token="token-a"))
    )
    store_b.merge_update(
        SettingsUpdate(jira=JiraSettings(base_url="b.atlassian.net", token="token-b"))
    )

    assert store_a.get_section("jira")["token"] == "token-a"
    assert store_b.get_section("jira")["token"] == "token-b"
    assert store_a.to_response().jira.base_url == "a.atlassian.net"
    assert store_b.to_response().jira.base_url == "b.atlassian.net"
    assert store_a.to_response().jira.token is None

    # Tokens are encrypted at rest in the database.
    row = db_session.get(UserSettings, user_a.id)
    assert row is not None
    stored_token = row.jira.get("token", "")
    assert is_encrypted_token(stored_token)
    assert "token-a" not in stored_token


def test_file_fallback_store_still_works(tmp_path):
    store = FileCredentialStore(tmp_path / "credentials.json")
    store.merge_update(
        SettingsUpdate(jira=JiraSettings(base_url="legacy.atlassian.net", token="legacy"))
    )
    assert store.get_section("jira")["token"] == "legacy"
    assert store.to_response().jira.token_set is True

    # On disk the token is encrypted, not plaintext.
    raw = json.loads((tmp_path / "credentials.json").read_text(encoding="utf-8"))
    assert is_encrypted_token(raw["jira"]["token"])
    assert "legacy" not in raw["jira"]["token"]


def test_db_lazy_migrates_plaintext_token(db_session):
    user = User(username="legacy", password_hash=hash_password("secret12"), is_admin=False)
    db_session.add(user)
    db_session.flush()
    db_session.add(
        UserSettings(
            user_id=user.id,
            jira={"base_url": "old.atlassian.net", "token": "plaintext-token"},
            git_provider={},
            testrail={},
            llm={},
        )
    )
    db_session.commit()

    store = DbCredentialStore(db_session, user.id)
    assert store.get_section("jira")["token"] == "plaintext-token"

    store.merge_update(SettingsUpdate(jira=JiraSettings(base_url="old.atlassian.net")))
    row = db_session.get(UserSettings, user.id)
    assert row is not None
    assert is_encrypted_token(row.jira["token"])
    assert store.get_section("jira")["token"] == "plaintext-token"
