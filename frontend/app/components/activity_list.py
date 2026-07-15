"""Recent activity list component."""

from datetime import datetime
from typing import Any

from nicegui import ui


def _format_time(item: dict[str, Any]) -> str:
    if time_label := item.get("time_label"):
        return time_label

    created_at = item.get("created_at")
    if not created_at:
        return ""

    if isinstance(created_at, str):
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            return created_at
    else:
        dt = created_at

    delta = datetime.now(dt.tzinfo) - dt if dt.tzinfo else datetime.now() - dt.replace(tzinfo=None)
    hours = int(delta.total_seconds() // 3600)
    if hours < 1:
        return "Just now"
    if hours < 24:
        return f"{hours}h ago"
    if hours < 48:
        return "Yesterday"
    return dt.strftime("%b %d")


def _activity_title(item: dict[str, Any]) -> str:
    if item.get("type") == "review":
        return f"PR #{item.get('pr_number', '?')} · {item.get('title', '')}"
    ticket_key = item.get("ticket_key", "")
    title = item.get("title", "")
    return f"{ticket_key} · {title}" if ticket_key else title


def _activity_count(item: dict[str, Any]) -> str:
    count = item.get("count", 0)
    if item.get("type") == "review":
        return f"{count} comment{'s' if count != 1 else ''}"
    return f"{count} case{'s' if count != 1 else ''}"


def activity_row(item: dict[str, Any]) -> None:
    is_review = item.get("type") == "review"
    badge_class = "badge-review" if is_review else "badge-tests"
    badge_label = "Review" if is_review else "Tests"

    with ui.element("div").classes("activity-row"):
        ui.label(badge_label).classes(badge_class)
        ui.label(_activity_title(item)).classes("activity-title")
        ui.label(_activity_count(item)).classes("activity-meta")
        ui.label(_format_time(item)).classes("activity-time")


def activity_panel(items: list[dict[str, Any]]) -> None:
    with ui.element("div").classes("panel-card w-full"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            ui.label("Recent activity").classes("text-lg font-bold")
            ui.button("View all", on_click=lambda: ui.notify("Full activity view coming soon")).props(
                "flat dense no-caps"
            ).classes("text-gray-600 border border-gray-300 rounded-lg px-3")

        if not items:
            ui.label("No recent activity.").classes("text-sm text-grey-7 py-4")
        for item in items:
            activity_row(item)
