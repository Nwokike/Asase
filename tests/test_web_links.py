"""Web link launch regressions.

Guards the two stacked defects that made every alert "Official Source"
link silently dead on web: (1) url_launcher was mounted native-only, so
the service guard dropped every click with no log; (2) fixed-URL buttons
must use the client-side OpenUrl action, because the click→Python round
trip outlives the browser's user-gesture window (iOS Safari drops it).
"""

import logging
from unittest.mock import AsyncMock, MagicMock

import flet as ft
import pytest
from flet.controls.context import _context_page
from flet_tree import walk

from core.actions import open_url_action
from core.controller import AppController
from core.device_services import DeviceServices


@pytest.fixture(autouse=True)
def _isolate_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))


def _page_mock(web=True):
    m = MagicMock()
    m.web = web
    m.session_id = None
    m.services = []
    m.render = MagicMock()
    m.update = MagicMock()
    m.run_task = MagicMock()
    m.client_storage = MagicMock()
    m.client_storage.get.return_value = None
    return m


def _bound_page():
    """Bind a fake page to the Flet context (what a runtime render has)."""
    token = _context_page.set(MagicMock())
    return token


def test_open_url_action_outside_runtime_returns_none():
    # Tree-building tests have no context page — callers keep on_click.
    assert open_url_action("https://example.com") is None
    assert open_url_action("") is None
    assert open_url_action(None) is None


def test_open_url_action_with_context_builds_client_action():
    token = _bound_page()
    try:
        act = open_url_action("https://example.com/src")
    finally:
        _context_page.reset(token)
    assert isinstance(act, ft.OpenUrl)
    assert act.url == "https://example.com/src"
    assert act.target == ft.UrlTarget.BLANK


def test_detail_sheet_source_button_carries_action_in_runtime():
    from components.hazard_map import build_event_detail_sheet

    event = {
        "type": "earthquake",
        "place": "Test quake",
        "latitude": 6.4,
        "longitude": 7.5,
        "magnitude": 4.2,
        "url": "https://earthquake.usgs.gov/event/abc",
    }
    token = _bound_page()
    try:
        sheet = build_event_detail_sheet(event, on_open_url=lambda u: None)
    finally:
        _context_page.reset(token)

    source = [
        b for b in walk(sheet) if isinstance(b, ft.TextButton) and b.content == "SOURCE"
    ]
    assert len(source) == 1
    btn = source[0]
    assert isinstance(btn.action, ft.OpenUrl)
    assert btn.action.url == "https://earthquake.usgs.gov/event/abc"
    # No Python path alongside the action — it would double-open.
    assert btn.on_click is None


def test_detail_sheet_source_button_falls_back_without_runtime():
    from components.hazard_map import build_event_detail_sheet

    event = {
        "type": "earthquake",
        "place": "Test quake",
        "latitude": 6.4,
        "longitude": 7.5,
        "url": "https://earthquake.usgs.gov/event/abc",
    }
    sheet = build_event_detail_sheet(event, on_open_url=lambda u: None)
    source = [
        b for b in walk(sheet) if isinstance(b, ft.TextButton) and b.content == "SOURCE"
    ]
    assert len(source) == 1
    assert source[0].action is None
    assert source[0].on_click is not None


async def test_launch_external_url_invokes_service():
    c = AppController(_page_mock())
    c.url_launcher = AsyncMock()
    await c.launch_external_url("https://example.com/x")
    c.url_launcher.launch_url.assert_awaited_once_with("https://example.com/x")


async def test_launch_without_service_logs_instead_of_silent(caplog):
    # The old guard returned with no log — every web click vanished silently.
    with caplog.at_level(logging.WARNING, logger="asase.device"):
        await DeviceServices.launch_url(None, "https://example.com/x")
    assert any("no UrlLauncher mounted" in r.message for r in caplog.records)
