"""Coverage for previously untested units (Batch S).

main.py init wiring, hooks, controller_ctx fields, changelog, AppStateCtx,
tasks done-callbacks, and the shell appbar builder.
"""

from dataclasses import fields
from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest

from state.controller_ctx import ControllerMethods


def test_controller_methods_has_all_expected_fields():
    names = {f.name for f in fields(ControllerMethods)}
    for expected in (
        "refresh_all",
        "select_coordinates",
        "locate_user",
        "save_setting",
        "toggle_bookmark",
        "show_map",
        "show_space",
        "show_report",
        "show_settings",
        "show_history",
        "go_home",
        "back",
        "dismiss_onboarding",
        "set_theme_mode",
        "open_report",
        "fetch_radius_history",
        "share_text",
        "launch_url",
        "navigate_tab",
        "tap_haptic",
    ):
        assert expected in names, f"missing ControllerMethods field: {expected}"


def test_changelog_notes_for_current_version():
    from core.changelog import notes_for
    from core.constants import APP_VERSION

    notes = notes_for(APP_VERSION)
    assert isinstance(notes, str) and len(notes) > 0


def test_changelog_unknown_version_falls_back():
    from core.changelog import notes_for

    assert isinstance(notes_for("0.0.0-nope"), str)


def test_app_state_ctx_wraps_singleton():
    from core.state import state
    from state.app_state import AppStateCtx

    # The context default IS the shared state object — components reading
    # the context with no provider mounted get the live singleton.
    assert AppStateCtx.default_value is state


@pytest.mark.asyncio
async def test_tasks_done_callback_logs_failure(caplog):
    import asyncio
    import logging

    from core.tasks import schedule

    async def _boom():
        raise RuntimeError("task-boom")

    with caplog.at_level(logging.WARNING, logger="asase.tasks"):
        task = schedule(_boom)  # no page -> create_task + logging callback
        try:
            await task
        except RuntimeError:
            pass
        await asyncio.sleep(0)  # let the done-callback fire
    assert any("Background task failed" in r.message for r in caplog.records)


def test_tasks_schedule_prefers_page_run_task():
    from unittest.mock import MagicMock

    from core.tasks import schedule

    async def _fn(a, b=0):
        return (a, b)

    page = MagicMock()
    result = schedule(_fn, 1, b=2, page=page)
    page.run_task.assert_called_once_with(_fn, 1, b=2)
    assert result is page.run_task.return_value


def test_build_appbar_report_and_space():
    from app_shell import _build_appbar

    controller = MagicMock()
    controller.go_home = MagicMock()
    report_bar = _build_appbar("report", 0, controller)
    assert isinstance(report_bar, ft.AppBar)
    space_bar = _build_appbar("space", 2, controller)
    assert isinstance(space_bar, ft.AppBar)
    assert _build_appbar("dashboard", 0, controller) is None


@pytest.mark.asyncio
async def test_main_wires_controller_lifecycle(tmp_path, monkeypatch):
    import main as app_main

    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    page = MagicMock()
    page.web = True  # skip native-only service registration
    page.views = [MagicMock()]
    with (
        patch.object(app_main.AppController, "init", new=AsyncMock()),
        patch.object(app_main.NetworkManager, "close", new=AsyncMock()),
    ):
        await app_main.main(page)
    assert page.on_error is not None
    assert page.on_close is not None
    assert page.on_disconnect is not None
    # Shutdown path flushes storage + ads + pool without raising.
    await page.on_close()


def test_use_debounce_hook_importable():
    from hooks.use_debounce import use_debounce

    assert callable(use_debounce)


def test_use_map_center_hook_importable():
    from hooks.use_map_center import use_map_center

    assert callable(use_map_center)
