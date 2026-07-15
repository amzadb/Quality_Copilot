"""Application shell — sidebar navigation and page wrapper."""

from nicegui import ui

from app.auth import logout, require_login
from app.components.styles import APP_CSS
from app.config import settings

NAV_ITEMS = [
    {"label": "Dashboard", "icon": "dashboard", "path": "/"},
    {"label": "Test cases", "icon": "checklist", "path": "/test-cases"},
    {"label": "Code review", "icon": "call_merge", "path": "/code-review"},
]

SETTINGS_ITEM = {"label": "Settings", "icon": "settings", "path": "/settings"}


def _nav_link(item: dict[str, str], active_path: str) -> None:
    is_active = active_path == item["path"] or (
        item["path"] != "/" and active_path.startswith(item["path"])
    )
    active_class = " active" if is_active else ""

    with ui.link(target=item["path"]).classes(f"nav-item{active_class} w-full no-underline"):
        ui.icon(item["icon"]).classes("text-xl")
        ui.label(item["label"])


def render_sidebar(active_path: str) -> None:
    with ui.left_drawer(value=True, fixed=True, bordered=True).props("width=250"):
        with ui.column().classes("w-full h-full px-4 pt-6 pb-4"):
            ui.label(settings.app_title).classes("text-xl font-bold mb-8 px-2")

            for item in NAV_ITEMS:
                _nav_link(item, active_path)

            ui.element("div").classes("flex-grow")

            _nav_link(SETTINGS_ITEM, active_path)
            ui.button("Logout", on_click=logout).classes("w-full mt-1").props(
                "flat dense color=negative"
            )


def apply_global_styles() -> None:
    ui.add_css(APP_CSS)


def page_shell(active_path: str) -> bool:
    """Set up layout chrome. Returns False if redirected to login."""
    if not require_login():
        return False
    apply_global_styles()
    render_sidebar(active_path)
    return True
