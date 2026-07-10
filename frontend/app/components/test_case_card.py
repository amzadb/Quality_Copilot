"""Individual generated test case card."""

from typing import Any

from nicegui import ui

TYPE_BADGE: dict[str, tuple[str, str]] = {
    "functional": ("Functional", "badge-functional"),
    "edge_case": ("Edge case", "badge-edge-case"),
    "negative": ("Negative", "badge-negative"),
}


def test_case_card(case: dict[str, Any]) -> None:
    case_id = case.get("id", "")
    title = case.get("title", "")
    expected = case.get("expected_result", "")
    type_key = case.get("type", "functional")
    badge_label, badge_class = TYPE_BADGE.get(type_key, ("Functional", "badge-functional"))

    with ui.element("div").classes("test-case-card"):
        with ui.row().classes("w-full items-start justify-between no-wrap gap-4"):
            ui.label(f"{case_id} · {title}").classes("test-case-title")
            ui.label(badge_label).classes(badge_class)
        ui.label(f"Expected: {expected}").classes("test-case-expected")
