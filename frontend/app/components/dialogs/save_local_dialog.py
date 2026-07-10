"""Save generated test cases to a local folder."""

from collections.abc import Callable
from datetime import date
from typing import Any

import httpx
from nicegui import ui

from app.api.client import api_client


def _default_folder(ticket_key: str) -> str:
    return f"output/test_cases/{ticket_key}/"


def _preview_filenames(ticket_key: str, formats: list[str]) -> str:
    today = date.today().isoformat()
    names: list[str] = []
    if "docx" in formats:
        names.append(f"{ticket_key}_{today}.docx")
    if "csv" in formats:
        names.append(f"{ticket_key}_{today}.csv")
    return "\n".join(names) if names else "No files selected"


def create_save_local_dialog() -> Callable[[str, str], None]:
    dialog = ui.dialog()
    run_id_holder: dict[str, str] = {"value": ""}
    ticket_key_holder: dict[str, str] = {"value": ""}

    with dialog, ui.card().classes("p-6 w-full max-w-lg"):
        ui.label("Save to local folder").classes("text-lg font-bold mb-2")

        folder_input = ui.input(label="Folder", placeholder="output/test_cases/PROJ-1042/").classes(
            "w-full"
        ).props("outlined dense")

        with ui.row().classes("gap-6 mt-2"):
            docx_checkbox = ui.checkbox("DOCX", value=True)
            csv_checkbox = ui.checkbox("CSV", value=True)

        ui.label("Preview").classes("text-sm text-gray-600 mt-2")
        preview_label = ui.label("").classes("dialog-preview w-full")

        def _refresh_preview() -> None:
            formats: list[str] = []
            if docx_checkbox.value:
                formats.append("docx")
            if csv_checkbox.value:
                formats.append("csv")
            preview_label.text = _preview_filenames(ticket_key_holder["value"], formats)

        docx_checkbox.on_value_change(_refresh_preview)
        csv_checkbox.on_value_change(_refresh_preview)

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat no-caps")

            async def confirm() -> None:
                formats: list[str] = []
                if docx_checkbox.value:
                    formats.append("docx")
                if csv_checkbox.value:
                    formats.append("csv")
                if not formats:
                    ui.notify("Select at least one format", type="warning")
                    return

                folder = (folder_input.value or "").strip()
                if not folder:
                    ui.notify("Enter a folder path", type="warning")
                    return

                try:
                    result = await api_client.save_test_cases_locally(
                        run_id_holder["value"], folder, formats
                    )
                except httpx.HTTPError as exc:
                    ui.notify(f"Save failed: {exc}", type="negative")
                    return

                files = result.get("saved_files", [])
                ui.notify(f"Saved {len(files)} file(s)", type="positive")
                dialog.close()

            ui.button("Save", on_click=confirm).props("unelevated no-caps").classes("btn-generate")

    def open_dialog(run_id: str, ticket_key: str) -> None:
        run_id_holder["value"] = run_id
        ticket_key_holder["value"] = ticket_key
        folder_input.value = _default_folder(ticket_key)
        docx_checkbox.value = True
        csv_checkbox.value = True
        _refresh_preview()
        dialog.open()

    return open_dialog
