"""Test cases page — fetch ticket, generate, and export workflow."""

import asyncio
from typing import Any

import httpx
from nicegui import ui

from app.api.client import MOCK_TICKET, api_client
from app.components.dialogs.attach_jira_dialog import create_attach_jira_dialog
from app.components.dialogs.save_local_dialog import create_save_local_dialog
from app.components.dialogs.testrail_upload_dialog import create_testrail_upload_dialog
from app.components.layout import page_shell
from app.components.status_banner import status_banner
from app.components.test_case_card import test_case_card

UI_BUILD = "2026-07-09-2"


async def render_test_cases() -> None:
    if not page_shell("/test-cases"):
        return

    state: dict[str, Any] = {
        "ticket": None,
        "run": None,
        "generating": False,
    }

    open_save_dialog = create_save_local_dialog()
    open_attach_dialog = create_attach_jira_dialog()
    open_testrail_dialog = create_testrail_upload_dialog()

    with ui.column().classes("page-content page-stack w-full gap-0"):
        with ui.element("div").classes("page-section--title w-full"):
            ui.label("Generate test cases").classes("page-title")
            ui.label(f"UI build {UI_BUILD}").classes("text-xs text-gray-400 mb-2")

        with ui.element("div").classes("page-section--fetch w-full"):
            with ui.element("div").classes("ticket-fetch-row"):
                ticket_input = ui.input(value="PROJ-1042", placeholder="PROJ-1042").classes(
                    "ticket-fetch-input"
                ).props("outlined dense")
                fetch_button = ui.button("Fetch ticket", icon="download").props("outline no-caps")

        with ui.element("div").classes("page-section--ticket w-full"):
            ticket_container = ui.column().classes("w-full")
            ticket_container.set_visibility(False)

        with ui.element("div").classes("page-section--loading w-full"):
            loading_container = ui.column().classes("w-full")
            loading_container.set_visibility(False)

        with ui.element("div").classes("page-section--results w-full"):
            results_container = ui.column().classes("w-full")
            results_container.set_visibility(False)

        with ui.element("div").classes("page-section--actions w-full"):
            actions_container = ui.row().classes("action-bar w-full")
            actions_container.set_visibility(False)

        async def show_ticket(ticket: dict[str, Any]) -> None:
            state["ticket"] = ticket
            ticket_container.clear()
            with ticket_container:
                with ui.element("div").classes("ticket-card w-full"):
                    ui.label(f"{ticket['key']} · {ticket['title']}").classes("ticket-card-title")
                    ui.label(ticket.get("description", "")).classes("ticket-card-description")

                    async def on_generate() -> None:
                        if state["generating"]:
                            return
                        state["generating"] = True
                        loading_container.clear()
                        with loading_container:
                            status_banner(
                                "Generating test cases with Claude, this can take up to a minute..."
                            )
                        loading_container.set_visibility(True)
                        results_container.set_visibility(False)
                        actions_container.set_visibility(False)

                        try:
                            run = await api_client.generate_test_cases(ticket["key"])
                        except httpx.HTTPError as exc:
                            ui.notify(f"Generation failed: {exc}", type="negative")
                            loading_container.set_visibility(False)
                            return
                        finally:
                            state["generating"] = False

                        if run.get("run_id", "").startswith("demo-"):
                            await asyncio.sleep(1.5)

                        loading_container.set_visibility(False)
                        state["run"] = run
                        show_results(run)

                    ui.button("Generate test cases", icon="auto_awesome", on_click=on_generate).props(
                        "no-caps unelevated"
                    ).classes("btn-generate")

            ticket_container.set_visibility(True)

        def show_results(run: dict[str, Any]) -> None:
            cases = run.get("test_cases", [])
            file_paths = run.get("file_paths") or {}
            saved_path = file_paths.get("docx") or file_paths.get("csv") or ""

            def _on_case_updated(updated: dict[str, Any]) -> None:
                if not state.get("run"):
                    return
                run_cases = state["run"].get("test_cases", [])
                for index, item in enumerate(run_cases):
                    if item.get("id") == updated.get("id"):
                        run_cases[index] = updated
                        break

            results_container.clear()
            with results_container:
                with ui.element("div").classes("results-panel w-full"):
                    with ui.element("div").classes("results-header"):
                        ui.label(f"Generated ({len(cases)})").classes("results-title")
                        if saved_path:
                            with ui.row().classes("saved-path items-center"):
                                ui.icon("folder").classes("text-base")
                                ui.label(saved_path)

                    for case in cases:
                        test_case_card(
                            case,
                            run_id=run.get("run_id"),
                            on_updated=_on_case_updated,
                        )

            results_container.set_visibility(True)

            actions_container.clear()
            with actions_container:
                ui.button(
                    "Save to local folder",
                    icon="save",
                    on_click=lambda: (
                        open_save_dialog(run["run_id"], ticket["key"])
                        if (run := state.get("run")) and (ticket := state.get("ticket"))
                        else ui.notify("Generate test cases first", type="warning")
                    ),
                ).props("outline no-caps")
                ui.button(
                    "Attach to JIRA",
                    icon="link",
                    on_click=lambda: (
                        open_attach_dialog(run["run_id"], ticket["key"])
                        if (run := state.get("run")) and (ticket := state.get("ticket"))
                        else ui.notify("Generate test cases first", type="warning")
                    ),
                ).props("outline no-caps")
                ui.button(
                    "Upload to TestRail",
                    icon="upload",
                    on_click=lambda: (
                        open_testrail_dialog(run["run_id"])
                        if (run := state.get("run"))
                        else ui.notify("Generate test cases first", type="warning")
                    ),
                ).props("outline no-caps")

            actions_container.set_visibility(True)

        async def on_fetch() -> None:
            key = (ticket_input.value or "").strip().upper()
            if not key:
                ui.notify("Enter a JIRA ticket key", type="warning")
                return
            ticket_input.value = key
            try:
                ticket = await api_client.fetch_jira_ticket(key)
            except httpx.HTTPError:
                ui.notify("Backend unreachable — using demo ticket data", type="warning")
                ticket = {**MOCK_TICKET, "key": key}
            await show_ticket(ticket)

        fetch_button.on_click(on_fetch)

        def _auto_fetch() -> None:
            asyncio.create_task(on_fetch())

        ui.timer(0.05, _auto_fetch, once=True)
