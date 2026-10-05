"""Version dialog + status-bar chip regressions.

Production crash guarded here: `show_version_dialog() got an unexpected
keyword argument 'controller'` — app_shell passed the palette's kwarg to
a function whose signature is only (page, update_data).
"""

import inspect
from unittest.mock import MagicMock

import flet as ft
from flet_tree import walk

from components.version_dialog import show_version_dialog


def test_version_dialog_signature_is_page_and_update_data_only():
    params = set(inspect.signature(show_version_dialog).parameters)
    assert params == {"page", "update_data"}


def test_show_version_dialog_opens_one_alertdialog():
    # Update data cleared so the deterministic "up to date" branch runs.
    from core.state import state

    saved = state.update_data
    state.update_data = None
    try:
        page = MagicMock()
        show_version_dialog(page)
    finally:
        state.update_data = saved
    assert page.show_dialog.call_count == 1
    dlg = page.show_dialog.call_args.args[0]
    assert isinstance(dlg, ft.AlertDialog)


def test_app_shell_version_entry_opens_dialog():
    """The exact production crash site: app_shell's version entry must
    call show_version_dialog with legal arguments only."""
    from app_shell import open_version_dialog

    page = MagicMock()
    open_version_dialog(page)
    assert page.show_dialog.call_count == 1


def test_status_bar_version_chip_fires_callback():
    from components.adaptive_nav import build_status_bar

    fired = []
    bar = build_status_bar(
        "Lagos",
        3,
        "Kp 4.2",
        lambda: None,
        on_open_version=lambda: fired.append(1),
        version_label="v1.0.3",
    )
    chips = [
        c
        for c in walk(bar)
        if getattr(c, "tooltip", None) == "What's New — version & changelog"
    ]
    assert len(chips) == 1
    chips[0].on_click(None)
    assert fired == [1]
