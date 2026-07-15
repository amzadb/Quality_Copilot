"""Auth API tests."""

from app.main import app
from app.models.base import get_db
from app.services.auth_service import seed_admin_user


def test_register_login_and_me(app_client):
    register = app_client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "password": "secret12", "email": "alice@example.com"},
    )
    assert register.status_code == 200
    body = register.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "alice"
    token = body["access_token"]

    me = app_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    login = app_client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "secret12"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_login_rejects_bad_password(app_client):
    app_client.post(
        "/api/v1/auth/register",
        json={"username": "bob", "password": "secret12"},
    )
    response = app_client.post(
        "/api/v1/auth/login",
        json={"username": "bob", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_settings_requires_auth(client):
    response = client.get("/api/v1/settings")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_duplicate_username_rejected(app_client):
    payload = {"username": "dupuser", "password": "secret12"}
    assert app_client.post("/api/v1/auth/register", json=payload).status_code == 200
    again = app_client.post("/api/v1/auth/register", json=payload)
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "USERNAME_TAKEN"


def test_seed_admin_user(app_client, monkeypatch):
    monkeypatch.setattr("app.config.settings.admin_username", "seedadmin")
    monkeypatch.setattr("app.config.settings.admin_password", "seedpass1")

    db_gen = app.dependency_overrides[get_db]()
    db = next(db_gen)
    try:
        user = seed_admin_user(db)
        assert user is not None
        assert user.username == "seedadmin"
        assert user.is_admin is True
    finally:
        db_gen.close()

    login = app_client.post(
        "/api/v1/auth/login",
        json={"username": "seedadmin", "password": "seedpass1"},
    )
    assert login.status_code == 200
