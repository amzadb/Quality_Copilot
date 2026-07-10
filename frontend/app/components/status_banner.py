"""Spinner + message row for long-running operations."""

from nicegui import ui


def status_banner(message: str) -> None:
    with ui.element("div").classes("loading-banner w-full"):
        ui.spinner(size="24px")
        ui.label(message)
