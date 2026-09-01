"""Tests for the interactive web splash patcher and web startup optimizations."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest

from core.controller import AppController
from core.state import state
from scripts.patch_web_splash import DISMISS_BRIDGE, SPLASH_HTML, patch_web


def test_splash_html_contains_adaptive_theme_and_walkthrough():
    # Adaptive theme CSS variables
    assert "--asase-bg: #0B0F17" in SPLASH_HTML
    assert "@media (prefers-color-scheme: light)" in SPLASH_HTML
    assert "--asase-bg: #F8FAFC" in SPLASH_HTML

    # Interactive 4-step walkthrough slides
    assert "Planetary Seismic Defense" in SPLASH_HTML
    assert "NASA EONET Events" in SPLASH_HTML
    assert "Hydrology & AQI Telemetry" in SPLASH_HTML
    assert "Grounded AI Briefings" in SPLASH_HTML

    # Navigation dots & touch swipe
    assert "asase-dots" in SPLASH_HTML
    assert "window.__asaseGo" in SPLASH_HTML
    assert "touchstart" in SPLASH_HTML
    assert "touchend" in SPLASH_HTML

    # Fast onboarding fallback loader & ready signal
    assert "window.__asaseEnter" in SPLASH_HTML
    assert "Booting Planetary Command..." in SPLASH_HTML
    assert "window.__asaseSignalReady" in SPLASH_HTML
    assert "asase_storage" in SPLASH_HTML
    assert "asase.onboarding_done" in SPLASH_HTML


def test_dismiss_bridge_contains_readiness_dispatch():
    assert "window.__asaseSignalReady" in DISMISS_BRIDGE
    assert "app.dartOnMessage(event.data)" in DISMISS_BRIDGE


def test_patch_web_function():
    with tempfile.TemporaryDirectory() as tmpdir:
        index_file = os.path.join(tmpdir, "index.html")
        python_js_file = os.path.join(tmpdir, "python.js")

        with open(index_file, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><head></head><body><p>App</p></body></html>")

        with open(python_js_file, "w", encoding="utf-8") as f:
            f.write("function onMsg() { app.dartOnMessage(event.data); }")

        with (
            patch("scripts.patch_web_splash.INDEX_PATHS", [index_file]),
            patch("scripts.patch_web_splash.PYTHON_JS_PATHS", [python_js_file]),
        ):
            res = patch_web()
            assert res == 0

        # Verify index.html was patched with preconnect & interactive splash
        with open(index_file, "r", encoding="utf-8") as f:
            patched_html = f.read()
        assert 'rel="preconnect" href="https://cdn.jsdelivr.net"' in patched_html
        assert 'id="asase-splash"' in patched_html
        assert "Planetary Seismic Defense" in patched_html

        # Verify python.js was patched with readiness bridge
        with open(python_js_file, "r", encoding="utf-8") as f:
            patched_pjs = f.read()
        assert "__asaseSignalReady" in patched_pjs


@pytest.mark.asyncio
async def test_controller_web_fast_path():
    # Mock web page
    mock_page = MagicMock(spec=ft.Page)
    mock_page.web = True
    mock_page.services = []
    mock_page.theme_mode = ft.ThemeMode.SYSTEM
    mock_page.window = MagicMock()
    mock_page.run_task = MagicMock()
    mock_page.render = MagicMock()

    controller = AppController(mock_page)

    with (
        patch.object(controller, "_load_saved_state", new=AsyncMock()),
        patch.object(controller, "refresh_all", new=AsyncMock()),
        patch.object(controller, "_telemetry_loop", new=AsyncMock()),
    ):
        await controller.init()

    # On web, mobile hardware services are skipped
    assert len(mock_page.services) == 0
    assert controller.connectivity is None
    assert controller.geolocator is None
    assert controller.haptics is None
    assert state.is_online is True

    # AppShell is mounted
    mock_page.render.assert_called_once()
