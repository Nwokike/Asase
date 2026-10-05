"""Tests for the interactive web splash patcher and web startup optimizations."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
import pytest

from core.controller import AppController
from core.state import state
from scripts.patch_web_splash import DISMISS_BRIDGE, SPLASH_HTML, patch_web


def test_splash_html_is_simple_theme_reactive_boot_screen():
    # App palette (core/theme.py AppColors) — dark + light, never guessed
    assert "#0B0F17" in SPLASH_HTML  # DARK_BG
    assert "#FAFAFA" in SPLASH_HTML  # LIGHT_BG
    assert "#F8FAFC" in SPLASH_HTML  # DARK_TEXT
    assert "#0F172A" in SPLASH_HTML  # LIGHT_TEXT
    assert "#10B981" in SPLASH_HTML  # PRIMARY (Emerald)

    # Simple loading state: brand icon, spinner, rotating status text
    assert "icon.png" in SPLASH_HTML
    assert "asase-spinner" in SPLASH_HTML
    assert "Starting Earth Intelligence" in SPLASH_HTML
    assert "Initializing telemetry core" in SPLASH_HTML
    assert "Connecting planetary feeds" in SPLASH_HTML

    # Theme follows the user's saved app theme, then OS preference
    assert "asase.theme" in SPLASH_HTML
    assert "prefers-color-scheme" in SPLASH_HTML
    assert 'classList.add("light")' in SPLASH_HTML

    # Auto-dismiss on engine readiness
    assert "window.__asaseSignalReady" in SPLASH_HTML
    assert "fade-out" in SPLASH_HTML

    # The splash must NOT act as onboarding — the in-app deck owns first-run
    assert "window.__asaseEnter" not in SPLASH_HTML
    assert "asase.onboarding_done" not in SPLASH_HTML
    assert "asase-dots" not in SPLASH_HTML


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

        # Verify index.html was patched with preconnect & boot splash
        with open(index_file, "r", encoding="utf-8") as f:
            patched_html = f.read()
        assert 'rel="preconnect" href="https://cdn.jsdelivr.net"' in patched_html
        assert 'id="asase-splash"' in patched_html
        assert "Initializing telemetry core" in patched_html

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

    # On web, mobile hardware services are skipped — but Geolocator stays
    # registered (browser Geolocation API) for user-gesture location entry,
    # Clipboard + UrlLauncher mount on every platform (browser APIs power
    # the dossier Copy button and every alert "Official Source" link), and
    # SharedPreferences backs the web storage tier.
    service_types = {type(s).__name__ for s in mock_page.services}
    assert service_types == {
        "Geolocator",
        "Clipboard",
        "UrlLauncher",
        "SharedPreferences",
    }
    assert controller.clipboard is not None
    assert controller.url_launcher is not None
    assert controller.connectivity is None
    assert controller.geolocator is not None
    assert controller.haptics is None
    assert state.is_online is True

    # Web is always the latest deployed build — the native update check
    # (version.json) must not run there.
    run_tasks = [c.args[0].__name__ for c in mock_page.run_task.call_args_list]
    assert "check_for_updates" not in run_tasks

    # AppShell is mounted
    mock_page.render.assert_called_once()


def test_splash_is_mission_control_staged_progress():
    # Hero percentage + step line + determinate bar
    assert 'id="asase-pct"' in SPLASH_HTML
    assert 'id="asase-step"' in SPLASH_HTML
    assert 'id="asase-bar-fill"' in SPLASH_HTML
    assert "of 4" in SPLASH_HTML
    # Four-row checklist — the three original status lines + first frame
    assert 'id="asase-checklist"' in SPLASH_HTML
    assert "Rendering first frame" in SPLASH_HTML
    assert "data-state" in SPLASH_HTML
    # Static anti-bounce microcopy (no rotating-timer gimmicks)
    assert "First load ~45" in SPLASH_HTML
    assert "runtime caches for next visit" in SPLASH_HTML

    # Real milestones only — window load, idempotent handshake, boot key,
    # 6s post-handshake watchdog, 45s absolute cap
    assert 'addEventListener("load"' in SPLASH_HTML
    assert '"asase.boot"' in SPLASH_HTML
    assert "setTimeout(finishFeeds, 6000)" in SPLASH_HTML
    assert "45000" in SPLASH_HTML
    # Stale boot key cleared at paint so repeat visits can't skip stage 3
    assert 'delete blob.data["asase.boot"]' in SPLASH_HTML
    # Monotonic band ceilings + in-band creep
    assert "CEIL" in SPLASH_HTML
    # Live OS theme flip updates the splash mid-load
    assert 'mq.addEventListener("change"' in SPLASH_HTML

    # App design language: brand gradient, glass surface, mono tabular %,
    # reduced-motion support
    assert "#111827" in SPLASH_HTML  # dark gradient/surface
    assert "JetBrains Mono" in SPLASH_HTML
    assert "tabular-nums" in SPLASH_HTML
    assert "prefers-reduced-motion" in SPLASH_HTML


@pytest.mark.asyncio
async def test_first_web_refresh_stamps_boot_key_once(tmp_path, monkeypatch):
    """_do_refresh stamps asase.boot (+flush) exactly once, on web only —
    the splash polls this key and its 6s watchdog degrades gracefully."""
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    mock_page = MagicMock(spec=ft.Page)
    mock_page.web = True
    mock_page.services = []
    mock_page.run_task = MagicMock()
    mock_page.render = MagicMock()
    mock_page.update = MagicMock()
    mock_page.theme_mode = ft.ThemeMode.SYSTEM
    mock_page.window = MagicMock()

    controller = AppController(mock_page)
    controller.storage = AsyncMock()

    with (
        patch.object(controller, "_fetch_global_feeds", new=AsyncMock()),
        patch.object(controller, "_fetch_local_feeds", new=AsyncMock()),
    ):
        await controller._do_refresh(True, True)
        await controller._do_refresh(True, True)  # loop refresh must not re-stamp

    assert controller.storage.set.call_count == 1
    key, value = controller.storage.set.call_args.args
    assert key == "asase.boot"
    assert isinstance(value, float) and value > 0
    assert controller.storage.flush.call_count == 1


@pytest.mark.asyncio
async def test_native_refresh_never_stamps_boot_key(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    mock_page = MagicMock(spec=ft.Page)
    mock_page.web = False
    mock_page.services = []
    mock_page.run_task = MagicMock()
    mock_page.render = MagicMock()
    mock_page.update = MagicMock()
    mock_page.theme_mode = ft.ThemeMode.SYSTEM
    mock_page.window = MagicMock()

    controller = AppController(mock_page)
    controller.storage = AsyncMock()

    with (
        patch.object(controller, "_fetch_global_feeds", new=AsyncMock()),
        patch.object(controller, "_fetch_local_feeds", new=AsyncMock()),
    ):
        await controller._do_refresh(True, True)

    controller.storage.set.assert_not_called()
