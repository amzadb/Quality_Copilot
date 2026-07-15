"""Dashboard page — metric cards and recent activity."""

import httpx
from nicegui import ui

from app.api.client import api_client
from app.components.activity_list import activity_panel
from app.components.layout import page_shell
from app.components.stat_card import stat_card


async def render_dashboard() -> None:
    if not page_shell("/"):
        return

    summary = await api_client.get_activity_summary()
    recent = await api_client.get_recent_activity(limit=20)

    with ui.dialog() as confirm_dialog, ui.card().classes("q-pa-md").style("min-width: 360px"):
        ui.label("Reset activity?").classes("text-lg font-bold")
        ui.label(
            "This clears dashboard metrics and the recent activity list. "
            "Counts will show as zero until you generate new test cases or reviews."
        ).classes("text-sm text-grey-7 my-2")
        with ui.row().classes("w-full justify-end gap-2 mt-2"):
            ui.button("Cancel", on_click=confirm_dialog.close).props("flat")

            async def confirm_reset() -> None:
                try:
                    await api_client.reset_activity()
                except httpx.HTTPError as exc:
                    ui.notify(f"Reset failed: {exc}", type="negative")
                    return
                confirm_dialog.close()
                ui.navigate.to("/")

            ui.button("Reset", on_click=confirm_reset).props("color=negative")

    with ui.column().classes("page-content w-full gap-6"):
        with ui.row().classes("w-full items-center justify-between no-wrap"):
            ui.label("Dashboard").classes("page-title mb-0")
            ui.button("Reset activity", on_click=confirm_dialog.open).props(
                "flat dense no-caps"
            ).classes("text-gray-600 border border-gray-300 rounded-lg px-3")

        with ui.row().classes("w-full gap-4 no-wrap"):
            stat_card("Tickets processed", str(summary.get("tickets_processed", 0)))
            stat_card("Test cases generated", str(summary.get("test_cases_generated", 0)))
            stat_card("PRs reviewed", str(summary.get("prs_reviewed", 0)))
            avg_seconds = summary.get("avg_review_time_seconds", 0)
            stat_card("Avg review time", f"{int(avg_seconds)}s")

        activity_panel(recent)

    if hasattr(ui, "page_scroller"):
        ui.page_scroller()
