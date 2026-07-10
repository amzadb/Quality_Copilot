"""Upload generated test cases to TestRail."""

from collections.abc import Callable
from typing import Any

import httpx
from nicegui import ui

from app.api.client import api_client


def create_testrail_upload_dialog() -> Callable[[str], None]:
    dialog = ui.dialog()
    run_id_holder: dict[str, str] = {"value": ""}
    projects_holder: dict[str, list[dict[str, Any]]] = {"items": []}
    suites_holder: dict[str, list[dict[str, Any]]] = {"items": []}

    with dialog, ui.card().classes("p-6 w-full max-w-lg"):
        ui.label("Upload to TestRail").classes("text-lg font-bold mb-2")

        project_select = ui.select(
            label="Project",
            options={},
            with_input=False,
        ).classes("w-full").props("outlined dense")

        mode_radio = ui.radio(
            {"existing": "Use existing suite", "new": "Create new suite"},
            value="existing",
        ).props("inline")

        suite_select = ui.select(
            label="Suite",
            options={},
            with_input=False,
        ).classes("w-full").props("outlined dense")

        new_suite_input = ui.input(
            label="New suite name",
            placeholder="SSO login flow",
        ).classes("w-full").props("outlined dense")

        suite_select.bind_visibility_from(mode_radio, "value", lambda v: v == "existing")
        new_suite_input.bind_visibility_from(mode_radio, "value", lambda v: v == "new")

        async def on_project_change(project_id: Any) -> None:
            if project_id is None:
                suites_holder["items"] = []
                suite_select.options = {}
                suite_select.value = None
                return
            try:
                suites = await api_client.list_testrail_suites(int(project_id))
            except httpx.HTTPError:
                ui.notify("Failed to load suites", type="negative")
                return
            suites_holder["items"] = suites
            suite_select.options = {s["id"]: s["name"] for s in suites}
            suite_select.value = suites[0]["id"] if suites else None

        project_select.on_value_change(on_project_change)

        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat no-caps")

            async def confirm() -> None:
                project_id = project_select.value
                if project_id is None:
                    ui.notify("Select a project", type="warning")
                    return

                payload: dict[str, Any] = {"project_id": int(project_id)}
                if mode_radio.value == "existing":
                    if suite_select.value is None:
                        ui.notify("Select a suite", type="warning")
                        return
                    payload["suite_id"] = int(suite_select.value)
                else:
                    name = (new_suite_input.value or "").strip()
                    if not name:
                        ui.notify("Enter a new suite name", type="warning")
                        return
                    payload["new_suite_name"] = name

                try:
                    result = await api_client.upload_to_testrail(run_id_holder["value"], **payload)
                except httpx.HTTPError as exc:
                    ui.notify(f"Upload failed: {exc}", type="negative")
                    return

                count = result.get("uploaded_count", 0)
                ui.notify(f"Uploaded {count} test case(s) to TestRail", type="positive")
                dialog.close()

            ui.button("Upload", on_click=confirm).props("unelevated no-caps").classes("btn-generate")

    async def _load_projects() -> None:
        try:
            projects = await api_client.list_testrail_projects()
        except httpx.HTTPError:
            ui.notify("Failed to load TestRail projects", type="negative")
            return
        projects_holder["items"] = projects
        project_select.options = {p["id"]: p["name"] for p in projects}
        if projects:
            project_select.value = projects[0]["id"]
            await on_project_change(projects[0]["id"])

    def open_dialog(run_id: str) -> None:
        run_id_holder["value"] = run_id
        mode_radio.value = "existing"
        new_suite_input.value = ""
        import asyncio

        asyncio.create_task(_load_projects())
        dialog.open()

    return open_dialog
