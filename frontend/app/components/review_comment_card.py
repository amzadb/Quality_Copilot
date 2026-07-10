"""Individual AI review comment card."""

from typing import Any

from nicegui import ui

SEVERITY_STYLE: dict[str, tuple[str, str, str]] = {
    "high": ("High", "badge-severity-high", "review-comment--high"),
    "medium": ("Medium", "badge-severity-medium", "review-comment--medium"),
    "style": ("Style", "badge-severity-style", "review-comment--style"),
}


def review_comment_card(comment: dict[str, Any]) -> None:
    file_name = comment.get("file", "")
    line = comment.get("line", 0)
    severity = comment.get("severity", "medium")
    text = comment.get("comment", "")

    label, badge_class, card_class = SEVERITY_STYLE.get(
        severity, ("Medium", "badge-severity-medium", "review-comment--medium")
    )

    with ui.element("div").classes(f"review-comment-card {card_class}"):
        with ui.row().classes("w-full items-center justify-between no-wrap gap-4"):
            ui.label(f"{file_name}:{line}").classes("review-comment-location")
            ui.label(label).classes(badge_class)
        ui.label(text).classes("review-comment-text")
