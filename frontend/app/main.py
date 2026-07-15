"""Quality Copilot NiceGUI application entry point."""

from pathlib import Path

from nicegui import ui

from app.config import settings
from app.notify_defaults import configure_notify_defaults
from app.pages.code_review import render_code_review
from app.pages.dashboard import render_dashboard
from app.pages.login import render_login
from app.pages.settings import render_settings
from app.pages.test_cases import render_test_cases


@ui.page("/login")
async def login_page() -> None:
    await render_login()


@ui.page("/")
async def dashboard_page() -> None:
    await render_dashboard()


@ui.page("/test-cases")
async def test_cases_page() -> None:
    await render_test_cases()


@ui.page("/code-review")
async def code_review_page() -> None:
    await render_code_review()


@ui.page("/settings")
async def settings_page() -> None:
    await render_settings()


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    print(f"Quality Copilot frontend starting from: {root}")
    print(f"Open http://127.0.0.1:{settings.port}/login")
    configure_notify_defaults()
    ui.run(
        title=settings.app_title,
        port=settings.port,
        reload=settings.reload,
        storage_secret=settings.storage_secret,
        favicon="🧪",
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
