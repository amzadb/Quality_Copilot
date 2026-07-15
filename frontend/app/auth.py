"""Session helpers for JWT stored in NiceGUI user storage."""

from nicegui import app, ui


def get_token() -> str | None:
    try:
        token = app.storage.user.get("token")
    except RuntimeError:
        return None
    return token if isinstance(token, str) and token else None


def get_username() -> str | None:
    try:
        username = app.storage.user.get("username")
    except RuntimeError:
        return None
    return username if isinstance(username, str) and username else None


def set_session(token: str, username: str) -> None:
    app.storage.user["token"] = token
    app.storage.user["username"] = username


def clear_session() -> None:
    try:
        app.storage.user.pop("token", None)
        app.storage.user.pop("username", None)
    except RuntimeError:
        pass


def require_login() -> bool:
    """Redirect to /login when no token. Returns False if redirecting."""
    if get_token():
        return True
    ui.navigate.to("/login")
    return False


def logout() -> None:
    clear_session()
    ui.navigate.to("/login")
