"""Default toast placement for NiceGUI notifications."""

from nicegui import ui


def configure_notify_defaults() -> None:
    """Show `ui.notify` toasts in the top-right unless a caller overrides position."""
    original = ui.notify

    def notify(message, *, position: str = "top-right", **kwargs):  # type: ignore[no-untyped-def]
        return original(message, position=position, **kwargs)

    ui.notify = notify  # type: ignore[method-assign]
