"""Attach generated test case files to a JIRA ticket."""

from collections.abc import Callable

import httpx
from nicegui import ui

from app.api.client import api_client


def create_attach_jira_dialog() -> Callable[[str, str], None]:
    dialog = ui.dialog()
    run_id_holder: dict[str, str] = {"value": ""}
    ticket_key_holder: dict[str, str] = {"value": ""}

    with dialog, ui.card().classes("p-6 w-full max-w-lg"):
        ui.label("Attach to JIRA").classes("text-lg font-bold mb-2")
        ticket_label = ui.label("").classes("text-sm text-gray-600 mb-2")

        with ui.row().classes("gap-6"):
            docx_checkbox = ui.checkbox("DOCX", value=True)
            csv_checkbox = ui.checkbox("CSV", value=False)

        comment_input = ui.textarea(
            label="Comment (optional)",
            placeholder="Attaching generated test cases for QA review.",
        ).classes("w-full").props("outlined dense")

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat no-caps")

            async def confirm() -> None:
                file_types: list[str] = []
                if docx_checkbox.value:
                    file_types.append("docx")
                if csv_checkbox.value:
                    file_types.append("csv")
                if not file_types:
                    ui.notify("Select at least one file type", type="warning")
                    return

                comment = (comment_input.value or "").strip() or None
                try:
                    result = await api_client.attach_to_jira(
                        ticket_key_holder["value"],
                        run_id_holder["value"],
                        file_types,
                        comment,
                    )
                except httpx.HTTPError as exc:
                    ui.notify(f"Attach failed: {exc}", type="negative")
                    return

                files = result.get("attached_files", [])
                ui.notify(f"Attached {len(files)} file(s) to JIRA", type="positive")
                dialog.close()

            ui.button("Attach", on_click=confirm).props("unelevated no-caps").classes("btn-generate")

    def open_dialog(run_id: str, ticket_key: str) -> None:
        run_id_holder["value"] = run_id
        ticket_key_holder["value"] = ticket_key
        ticket_label.text = f"Ticket: {ticket_key}"
        docx_checkbox.value = True
        csv_checkbox.value = False
        comment_input.value = "Attaching generated test cases for QA review."
        dialog.open()

    return open_dialog
