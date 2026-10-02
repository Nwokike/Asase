"""Batch Q regressions: pin, snackbar coalescing."""

from pathlib import Path
from unittest.mock import MagicMock

import flet as ft

from core.notify import reset_snack_dedup, show_snack


def test_flet_family_pinned_exact():
    import tomllib

    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    deps = pyproject["project"]["dependencies"]
    for name in (
        "flet",
        "flet-ads",
        "flet-map",
        "flet-geolocator",
        "flet-charts",
    ):
        pinned = [d for d in deps if d.startswith(f"{name}==")]
        assert len(pinned) == 1, f"{name} not pinned exact: {deps}"
        assert pinned[0] == f"{name}==1.0.3"


def _page():
    page = MagicMock()
    del page.show_snack_bar
    del page.open
    return page


def test_snack_burst_coalesced():
    reset_snack_dedup()
    page = _page()
    show_snack(page, "Offline — retrying")
    show_snack(page, "Offline — retrying")
    show_snack(page, "Offline — retrying")
    assert page.show_dialog.call_count == 1
    reset_snack_dedup()


def test_snack_distinct_messages_all_show():
    reset_snack_dedup()
    page = _page()
    show_snack(page, "Alpha")
    show_snack(page, "Beta")
    assert page.show_dialog.call_count == 2
    reset_snack_dedup()


def test_snack_same_message_new_color_shows():
    reset_snack_dedup()
    page = _page()
    show_snack(page, "Note", bgcolor=ft.Colors.RED)
    show_snack(page, "Note", bgcolor=ft.Colors.GREEN)
    assert page.show_dialog.call_count == 2
    reset_snack_dedup()


def test_use_dialog_hook_exists_and_settings_uses_it():
    # use_dialog is render-hook-only: verify the hook exists in 1.0.3 and
    # the settings clear-history flow is driven by it (no manual
    # show/pop for that dialog).
    assert callable(ft.use_dialog)
    src = Path("src/screens/settings_screen.py").read_text()
    assert "ft.use_dialog(" in src
    assert "set_show_clear_confirm" in src
