"""Snackbar/dialog delivery on Flet 1.0.3.

Regression tests: Page has no ``show_snack_bar`` (or ``open``) in 1.0.3 —
only ``show_dialog``/``pop_dialog`` — and SnackBar subclasses DialogControl,
so show_snack must take the show_dialog path without raising. Also pins
the burst-coalescing window: it anchors to the last SHOWN toast, so a
persistent error stream re-announces instead of going silent forever.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import flet as ft

from components import version_dialog
from core import notify as notify_mod
from core.notify import reset_snack_dedup, show_snack


def _page():
    page = MagicMock()
    # Mirror the real 1.0.3 Page surface: no show_snack_bar, no open.
    del page.show_snack_bar
    del page.open
    return page


def _clock(monkeypatch, start: float = 100.0) -> dict:
    t = {"now": start}
    monkeypatch.setattr(notify_mod, "time", SimpleNamespace(monotonic=lambda: t["now"]))
    return t


def test_show_snack_uses_show_dialog_path():
    page = _page()
    show_snack(page, "hello")
    assert page.show_dialog.call_count == 1
    snack = page.show_dialog.call_args.args[0]
    assert isinstance(snack, ft.SnackBar)


def test_show_snack_none_page_does_not_raise():
    show_snack(None, "dropped")  # logs + returns


def test_show_snack_dialog_failure_does_not_raise():
    page = _page()
    page.show_dialog.side_effect = RuntimeError("boom")
    show_snack(page, "hello")  # logs + returns


def test_snack_duplicate_within_window_coalesced(monkeypatch):
    reset_snack_dedup()
    page = _page()
    t = _clock(monkeypatch)
    show_snack(page, "Offline — retrying")  # shown at t=100
    t["now"] = 101.9  # within the 2s window
    show_snack(page, "Offline — retrying")
    assert page.show_dialog.call_count == 1
    reset_snack_dedup()


def test_snack_window_does_not_slide_on_coalesce(monkeypatch):
    """A persistent error stream re-announces once the window from the
    last SHOWN toast passes — it never goes silent after the toast
    auto-dismisses."""
    reset_snack_dedup()
    page = _page()
    t = _clock(monkeypatch)
    show_snack(page, "Offline — retrying")  # shown at t=100
    t["now"] = 101.9
    show_snack(page, "Offline — retrying")  # coalesced; window NOT extended
    t["now"] = 102.1  # > 2s from the shown toast
    show_snack(page, "Offline — retrying")
    assert page.show_dialog.call_count == 2
    reset_snack_dedup()


def test_snack_different_message_always_shows(monkeypatch):
    reset_snack_dedup()
    page = _page()
    t = _clock(monkeypatch)
    show_snack(page, "Offline — retrying")
    t["now"] = 101.0
    show_snack(page, "Back online")  # distinct message bypasses the window
    assert page.show_dialog.call_count == 2
    reset_snack_dedup()


def test_page_has_no_legacy_snackbar_api():
    """Pin the 1.0.3 surface so a future Flet change is noticed, not silent."""
    assert not hasattr(ft.Page, "show_snack_bar")
    assert not hasattr(ft.Page, "open")
    assert issubclass(ft.SnackBar, ft.DialogControl)


async def test_check_from_dialog_up_to_date_path():
    from services import update_service

    page = _page()
    with patch.object(
        update_service.UpdateService, "check_for_update", return_value=None
    ):
        await version_dialog.check_from_dialog(page)
    assert page.show_dialog.call_count == 1
    snack = page.show_dialog.call_args.args[0]
    assert isinstance(snack, ft.SnackBar)
