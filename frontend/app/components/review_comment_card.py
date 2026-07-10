"""Individual AI review comment card with triage actions."""

from collections.abc import Callable
from typing import Any

import httpx
from nicegui import ui

from app.api.client import api_client

SEVERITY_STYLE: dict[str, tuple[str, str, str]] = {
    "high": ("High", "badge-severity-high", "review-comment--high"),
    "medium": ("Medium", "badge-severity-medium", "review-comment--medium"),
    "style": ("Style", "badge-severity-style", "review-comment--style"),
}


def _severity_classes(severity: str, triage_status: str | None) -> str:
    _, _, base_class = SEVERITY_STYLE.get(
        severity, ("Medium", "badge-severity-medium", "review-comment--medium")
    )
    classes = f"review-comment-card {base_class}"
    if triage_status == "dismissed":
        classes += " review-comment--dismissed"
    elif triage_status == "addressed":
        classes += " review-comment--addressed"
    return classes


def review_comment_card(
    comment: dict[str, Any],
    *,
    run_id: str | None = None,
    on_triage_change: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    file_name = comment.get("file", "")
    line = comment.get("line", 0)
    severity = comment.get("severity", "medium")
    text = comment.get("comment", "")

    label, badge_class, _ = SEVERITY_STYLE.get(
        severity, ("Medium", "badge-severity-medium", "review-comment--medium")
    )

    with ui.element("div").classes(_severity_classes(severity, comment.get("triage_status"))) as card_el:
        with ui.row().classes("w-full items-center justify-between no-wrap gap-4"):
            ui.label(f"{file_name}:{line}").classes("review-comment-location")
            ui.label(label).classes(badge_class)
        ui.label(text).classes("review-comment-text")
        triage_row = ui.row().classes("review-comment-triage items-center gap-2 mt-3")

        def _render_triage() -> None:
            triage_row.clear()
            status = comment.get("triage_status")
            with triage_row:
                if status == "dismissed":
                    ui.label("Dismissed").classes(
                        "review-triage-status review-triage-status--dismissed"
                    )
                elif status == "addressed":
                    ui.label("Addressed").classes(
                        "review-triage-status review-triage-status--addressed"
                    )

                if run_id and on_triage_change and comment.get("id"):

                    async def _set_triage(next_status: str) -> None:
                        current = comment.get("triage_status")
                        new_status = None if current == next_status else next_status
                        if new_status:
                            try:
                                updated = await api_client.update_review_comment(
                                    run_id, comment["id"], new_status
                                )
                            except httpx.HTTPError as exc:
                                ui.notify(f"Update failed: {exc}", type="negative")
                                return
                            comment.update(updated)
                        else:
                            comment["triage_status"] = None

                        on_triage_change(comment)
                        card_el.classes(
                            replace=_severity_classes(severity, comment.get("triage_status"))
                        )
                        _render_triage()

                    dismiss_props = "flat dense no-caps size=sm"
                    addressed_props = "flat dense no-caps size=sm"
                    if status == "dismissed":
                        dismiss_props = "unelevated dense no-caps size=sm color=grey-7"
                    if status == "addressed":
                        addressed_props = "unelevated dense no-caps size=sm color=positive"

                    ui.button(
                        "Dismiss",
                        icon="close",
                        on_click=lambda: _set_triage("dismissed"),
                    ).props(dismiss_props)
                    ui.button(
                        "Addressed",
                        icon="check",
                        on_click=lambda: _set_triage("addressed"),
                    ).props(addressed_props)

        _render_triage()
