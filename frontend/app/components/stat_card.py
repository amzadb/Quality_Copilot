"""Dashboard stat card component."""

from nicegui import ui


def stat_card(label: str, value: str) -> None:
    with ui.element("div").classes("stat-card"):
        ui.label(label).classes("stat-label")
        ui.label(value).classes("stat-value")
