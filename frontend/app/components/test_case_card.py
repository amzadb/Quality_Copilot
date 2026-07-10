"""Individual generated test case card with optional inline edit."""

from collections.abc import Callable
from typing import Any

import httpx
from nicegui import ui

from app.api.client import api_client

TYPE_BADGE: dict[str, tuple[str, str]] = {
    "functional": ("Functional", "badge-functional"),
    "edge_case": ("Edge case", "badge-edge-case"),
    "negative": ("Negative", "badge-negative"),
}

TYPE_OPTIONS = {
    "functional": "Functional",
    "edge_case": "Edge case",
    "negative": "Negative",
}


def test_case_card(
    case: dict[str, Any],
    *,
    run_id: str | None = None,
    on_updated: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    editable = bool(run_id and on_updated)

    with ui.element("div").classes("test-case-card"):
        view_container = ui.column().classes("w-full gap-0")
        edit_container = ui.column().classes("w-full gap-2")
        edit_container.set_visibility(False)

        def _badge_label(type_key: str) -> tuple[str, str]:
            return TYPE_BADGE.get(type_key, ("Functional", "badge-functional"))

        def _render_view() -> None:
            view_container.clear()
            case_id = case.get("id", "")
            title = case.get("title", "")
            expected = case.get("expected_result", "")
            type_key = case.get("type", "functional")
            badge_label, badge_class = _badge_label(type_key)

            with view_container:
                with ui.row().classes("w-full items-start justify-between no-wrap gap-4"):
                    ui.label(f"{case_id} · {title}").classes("test-case-title")
                    with ui.row().classes("items-center gap-2 no-wrap"):
                        ui.label(badge_label).classes(badge_class)
                        if editable:
                            ui.button(icon="edit", on_click=_start_edit).props(
                                "flat dense round size=sm"
                            ).classes("test-case-edit-btn")
                ui.label(f"Expected: {expected}").classes("test-case-expected")

        def _cancel_edit() -> None:
            edit_container.set_visibility(False)
            view_container.set_visibility(True)

        def _start_edit() -> None:
            if not editable:
                return
            edit_container.clear()
            with edit_container:
                ui.label(f"Edit {case.get('id', '')}").classes("text-sm font-bold text-gray-700")
                title_input = ui.input(label="Title", value=case.get("title", "")).classes(
                    "w-full"
                ).props("outlined dense")
                type_input = ui.select(
                    TYPE_OPTIONS,
                    label="Type",
                    value=case.get("type", "functional"),
                ).classes("w-full").props("outlined dense")
                steps_input = ui.textarea(
                    label="Steps (one per line)",
                    value="\n".join(case.get("steps", [])),
                ).classes("w-full").props("outlined dense rows=4")
                expected_input = ui.textarea(
                    label="Expected result",
                    value=case.get("expected_result", ""),
                ).classes("w-full").props("outlined dense rows=2")

                with ui.row().classes("w-full justify-end gap-2 mt-1"):
                    ui.button("Cancel", on_click=_cancel_edit).props("flat no-caps")

                    async def save() -> None:
                        title = (title_input.value or "").strip()
                        expected = (expected_input.value or "").strip()
                        steps = [
                            s.strip() for s in (steps_input.value or "").splitlines() if s.strip()
                        ]
                        if not title:
                            ui.notify("Title is required", type="warning")
                            return
                        if not expected:
                            ui.notify("Expected result is required", type="warning")
                            return

                        payload: dict[str, Any] = {
                            "title": title,
                            "type": type_input.value,
                            "steps": steps,
                            "expected_result": expected,
                        }
                        try:
                            updated = await api_client.update_test_case(
                                run_id, case["id"], payload
                            )
                        except httpx.HTTPError as exc:
                            ui.notify(f"Update failed: {exc}", type="negative")
                            return

                        case.clear()
                        case.update(updated)
                        if on_updated:
                            on_updated(updated)
                        _cancel_edit()
                        _render_view()
                        ui.notify("Test case updated", type="positive")

                    ui.button("Save", on_click=save).props("unelevated no-caps").classes(
                        "btn-generate"
                    )

            view_container.set_visibility(False)
            edit_container.set_visibility(True)

        _render_view()
