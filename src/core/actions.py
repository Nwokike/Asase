"""Client-side actions that must run inside the browser's user gesture."""

from __future__ import annotations

import flet as ft


def open_url_action(url: str | None) -> ft.OpenUrl | None:
    """Gesture-safe URL open (Flet ClientAction) for fixed-at-build URLs.

    Runs on the client inside the original click, so web browsers accept
    the new tab — the click→Python round trip outlives the gesture window
    and iOS Safari silently drops it. Returns None outside a running Flet
    app (tree-building tests have no context page); callers keep their
    on_click Python path as the fallback in that case.
    """
    if not url:
        return None
    try:
        return ft.OpenUrl(str(url), target=ft.UrlTarget.BLANK)
    except RuntimeError:
        # No page context (tests building controls outside a runtime).
        return None
