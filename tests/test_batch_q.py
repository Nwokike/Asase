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
        assert pinned[0] == f"{name}==1.0.4"


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


def test_use_dialog_hook_exists():
    # use_dialog is render-hook-only in Flet 1.0.3 — pin the real API
    # surface (no manual show/pop path exists).
    assert callable(ft.use_dialog)
    assert not hasattr(ft.Page, "show_snack_bar")


def test_clear_confirm_dialog_built_and_wired():
    from flet_tree import walk, walk_texts

    from screens.settings_screen import build_clear_confirm_dialog

    cancelled, cleared = [], []
    dlg = build_clear_confirm_dialog(
        lambda: cancelled.append(1), lambda: cleared.append(1)
    )

    texts = [t.value for t in walk_texts(dlg)]
    assert "Clear Search History?" in texts
    assert "This will remove all recent location queries." in texts

    buttons = [b for b in walk(dlg) if isinstance(b, (ft.TextButton, ft.FilledButton))]
    # Flet 1.0.3 stores the label as a raw string in `content`.
    assert [b.content for b in buttons] == ["Cancel", "Clear All"]

    buttons[0].on_click(MagicMock())
    assert cancelled == [1] and cleared == []
    buttons[1].on_click(MagicMock())
    assert cancelled == [1] and cleared == [1]


def test_clear_all_style_is_destructive():
    from flet_tree import walk

    from core.theme import AppColors
    from screens.settings_screen import build_clear_confirm_dialog

    dlg = build_clear_confirm_dialog(lambda: None, lambda: None)
    filled = [b for b in walk(dlg) if isinstance(b, ft.FilledButton)]
    assert len(filled) == 1
    assert filled[0].style.bgcolor == AppColors.ERROR
