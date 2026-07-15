"""Default toast placement for NiceGUI notifications."""

from nicegui import ui

_configured = False


def configure_notify_defaults() -> None:
    """Show `ui.notify` toasts in the top-right unless a caller overrides position."""
    global _configured
    if _configured:
        return

    original = ui.notify

    def notify(message, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("position", "top-right")
        return original(message, *args, **kwargs)

    ui.notify = notify  # type: ignore[method-assign]
    _configured = True
