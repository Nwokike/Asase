"""Snackbar/dialog delivery on Flet 1.0.3.

Regression tests: Page has no ``show_snack_bar`` (or ``open``) in 1.0.3 —
only ``show_dialog``/``pop_dialog`` — and SnackBar subclasses DialogControl,
so show_snack must take the show_dialog path without raising.
"""

from unittest.mock import MagicMock, patch

import flet as ft

from components import version_dialog
from core.notify import show_snack


def _page():
    page = MagicMock()
    # Mirror the real 1.0.3 Page surface: no show_snack_bar, no open.
    del page.show_snack_bar
    del page.open
    return page


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


def test_page_has_no_legacy_snackbar_api():
    """Pin the 1.0.3 surface so a future Flet change is noticed, not silent."""
    assert not hasattr(ft.Page, "show_snack_bar")
    assert not hasattr(ft.Page, "open")
    assert issubclass(ft.SnackBar, ft.DialogControl)


def test_check_from_dialog_up_to_date_path():
    import asyncio

    from services import update_service

    page = _page()
    with patch.object(
        update_service.UpdateService, "check_for_update", return_value=None
    ):
        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
            version_dialog.check_from_dialog(page)
        )
    assert page.show_dialog.call_count == 1
    snack = page.show_dialog.call_args.args[0]
    assert isinstance(snack, ft.SnackBar)
