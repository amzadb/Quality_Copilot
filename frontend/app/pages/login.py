"""Login, self-registration, and password reset page."""

from nicegui import ui

from app.api.client import api_client
from app.auth import get_token, set_session
from app.components.styles import APP_CSS
from app.config import settings


async def render_login() -> None:
    ui.add_css(APP_CSS)

    if get_token():
        ui.navigate.to("/")
        return

    async def do_login() -> None:
        login_error.set_visibility(False)
        username = (login_user.value or "").strip()
        password = login_pass.value or ""
        if not username or not password:
            login_error.set_text("Username and password are required.")
            login_error.set_visibility(True)
            return
        try:
            data = await api_client.login(username, password)
        except Exception as exc:  # noqa: BLE001 — show user-facing message
            login_error.set_text(_login_error_message(exc))
            login_error.set_visibility(True)
            return
        set_session(data["access_token"], data["user"]["username"])
        ui.navigate.to("/")

    async def do_register() -> None:
        register_error.set_visibility(False)
        username = (reg_user.value or "").strip()
        password = reg_pass.value or ""
        email = (reg_email.value or "").strip() or None
        if not username or not password:
            register_error.set_text("Username and password are required.")
            register_error.set_visibility(True)
            return
        if len(password) < 6:
            register_error.set_text("Password must be at least 6 characters.")
            register_error.set_visibility(True)
            return
        try:
            data = await api_client.register(username, password, email=email)
        except Exception as exc:  # noqa: BLE001
            register_error.set_text(_error_message(exc, "Registration failed."))
            register_error.set_visibility(True)
            return
        set_session(data["access_token"], data["user"]["username"])
        ui.navigate.to("/")

    async def do_reset() -> None:
        reset_error.text = ""
        reset_error.set_visibility(False)
        reset_success.text = ""
        reset_success.set_visibility(False)
        username = (reset_user.value or "").strip()
        new_password = reset_new.value or ""
        confirm_password = reset_confirm.value or ""
        if not username or not new_password:
            reset_error.text = "Username and new password are required."
            reset_error.set_visibility(True)
            return
        if len(new_password) < 6:
            reset_error.text = "New password must be at least 6 characters."
            reset_error.set_visibility(True)
            return
        if new_password != confirm_password:
            reset_error.text = "New password and confirmation do not match."
            reset_error.set_visibility(True)
            return
        try:
            result = await api_client.reset_password(username, new_password)
        except Exception as exc:  # noqa: BLE001
            reset_error.text = _error_message(exc, "Password reset failed.")
            reset_error.set_visibility(True)
            return

        message = "Password updated successfully. You can log in with your new password."
        if isinstance(result, dict):
            api_message = result.get("message")
            if isinstance(api_message, str) and api_message.strip():
                message = api_message

        reset_new.value = ""
        reset_confirm.value = ""
        reset_success.text = message
        reset_success.set_visibility(True)

    with ui.column().classes("w-full items-center justify-center").style(
        "min-height: 100vh; padding: 2rem;"
    ):
        with ui.card().classes("w-full").style("max-width: 420px; padding: 1.75rem;"):
            ui.label(settings.app_title).classes("text-2xl font-bold")

            with ui.tabs().classes("w-full") as tabs:
                login_tab = ui.tab("Login")
                register_tab = ui.tab("Sign up")
                reset_tab = ui.tab("Reset password")

            with ui.tab_panels(tabs, value=login_tab).classes("w-full"):
                with ui.tab_panel(login_tab):
                    login_user = ui.input("Username").classes("w-full").props("outlined dense")
                    login_pass = (
                        ui.input("Password", password=True, password_toggle_button=True)
                        .classes("w-full")
                        .props("outlined dense")
                    )
                    ui.button("Log in", on_click=do_login).classes("w-full mt-2").props(
                        "color=primary"
                    )
                    login_error = ui.label("").classes("text-negative text-sm mt-2")
                    login_error.set_visibility(False)

                with ui.tab_panel(register_tab):
                    reg_user = ui.input("Username").classes("w-full").props("outlined dense")
                    reg_email = ui.input("Email (optional)").classes("w-full").props("outlined dense")
                    reg_pass = (
                        ui.input("Password", password=True, password_toggle_button=True)
                        .classes("w-full")
                        .props("outlined dense")
                    )
                    ui.button("Create account", on_click=do_register).classes("w-full mt-2").props(
                        "color=primary"
                    )
                    register_error = ui.label("").classes("text-negative text-sm mt-2")
                    register_error.set_visibility(False)

                with ui.tab_panel(reset_tab):
                    ui.label("Enter your username and a new password.").classes(
                        "text-sm text-grey-7 mb-2"
                    )
                    reset_user = ui.input("Username").classes("w-full").props("outlined dense")
                    reset_new = (
                        ui.input("New password", password=True, password_toggle_button=True)
                        .classes("w-full")
                        .props("outlined dense")
                    )
                    reset_confirm = (
                        ui.input("Confirm new password", password=True, password_toggle_button=True)
                        .classes("w-full")
                        .props("outlined dense")
                    )
                    ui.button("Reset password", on_click=do_reset).classes("w-full mt-2").props(
                        "color=primary"
                    )
                    reset_error = (
                        ui.label("")
                        .classes("text-sm mt-2")
                        .style("color: #c62828;")
                    )
                    reset_error.set_visibility(False)
                    reset_success = (
                        ui.label("")
                        .classes("text-sm mt-2")
                        .style("color: #2e7d32; font-weight: 500;")
                    )
                    reset_success.set_visibility(False)


def _login_error_message(exc: Exception) -> str:
    import httpx

    if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 401:
        return "Invalid username or password."
    return _error_message(exc, "Login failed.")


def _error_message(exc: Exception, fallback: str) -> str:
    import httpx

    if isinstance(exc, httpx.HTTPStatusError):
        try:
            body = exc.response.json()
            msg = body.get("error", {}).get("message")
            if isinstance(msg, str) and msg:
                return msg
        except Exception:  # noqa: BLE001
            pass
        return f"{fallback} (HTTP {exc.response.status_code})"
    return fallback
