"""Dashboard page — metric cards and recent activity."""

from nicegui import ui

from app.api.client import api_client
from app.components.activity_list import activity_panel
from app.components.layout import page_shell
from app.components.stat_card import stat_card


async def render_dashboard() -> None:
    page_shell("/")

    summary = await api_client.get_activity_summary()
    recent = await api_client.get_recent_activity(limit=20)

    with ui.column().classes("page-content w-full gap-6"):
        with ui.row().classes("w-full gap-4 no-wrap"):
            stat_card("Tickets processed", str(summary.get("tickets_processed", 0)))
            stat_card("Test cases generated", str(summary.get("test_cases_generated", 0)))
            stat_card("PRs reviewed", str(summary.get("prs_reviewed", 0)))
            avg_seconds = summary.get("avg_review_time_seconds", 0)
            stat_card("Avg review time", f"{int(avg_seconds)}s")

        activity_panel(recent)

    if hasattr(ui, "page_scroller"):
        ui.page_scroller()
