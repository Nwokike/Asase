"""AppShell — Top-level shell managing tabs, sub-views, and chrome sync."""

from __future__ import annotations

import logging

import flet as ft
from flet import Control
from flet import context as flet_context

from components.adaptive_nav import (
    build_navigation_bar,
    build_navigation_rail,
    build_sidebar,
    build_status_bar,
    window_class,
)
from core import tokens
from core.constants import APP_VERSION, STORAGE_SIDEBAR_COLLAPSED
from core.theme import is_dark_mode
from screens.home_screen import HomeScreen
from screens.map_screen import MapScreen
from screens.report_screen import ReportScreen
from screens.settings_screen import SettingsScreen
from screens.space_screen import SpaceScreen
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.shell")

_TAB_NAMES = ("Radar", "Full Map", "Space", "History", "Settings")
_TAB_ICONS = (
    ft.Icons.DASHBOARD_ROUNDED,
    ft.Icons.MAP_ROUNDED,
    ft.Icons.PUBLIC_ROUNDED,
    ft.Icons.HISTORY_ROUNDED,
    ft.Icons.SETTINGS_ROUNDED,
)

# Name → index lookup so navigation wiring cannot silently swap when tabs
# are reordered; always resolve through this instead of magic indices.
_TAB_INDEX = {name: i for i, name in enumerate(_TAB_NAMES)}


def resolve_dashboard_screen(active_tab: int):
    """Map a dashboard tab index to its screen factory.

    Pure function (no hooks) so route wiring is unit-testable.
    Unknown indices fall through to Settings, matching shell history.
    """
    if active_tab == 0:
        return HomeScreen
    if active_tab == 1:
        return MapScreen
    if active_tab == 2:
        return SpaceScreen
    if active_tab == _TAB_INDEX["History"]:
        from screens.history_screen import HistoryScreen

        return HistoryScreen
    return SettingsScreen


def open_version_dialog(page=None):
    """Status-bar version chip entry point.

    Module-level (not a closure) so the exact call site is unit-testable —
    `show_version_dialog` takes (page, update_data) only, unlike
    `show_command_palette`, which does accept a controller kwarg.
    """
    from components.version_dialog import show_version_dialog

    show_version_dialog(page if page is not None else flet_context.page)


def _build_appbar(
    active_view: str, active_tab: int, controller, include_title: bool = True
) -> ft.AppBar | None:
    """Back button for overlay views. ``include_title=False`` when the side
    chrome status bar already carries the title (prevents a double header)."""
    if active_view == "report":
        return ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                on_click=lambda _: controller.go_home() if controller.go_home else None,
            ),
            title=ft.Text(
                "Location Risk Dossier", size=tokens.FONT_LG, weight=ft.FontWeight.W_600
            )
            if include_title
            else None,
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
        )

    if active_view == "space":
        return ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                on_click=lambda _: controller.go_home() if controller.go_home else None,
            ),
            title=ft.Text(
                "Planetary Magnetosphere",
                size=tokens.FONT_LG,
                weight=ft.FontWeight.W_600,
            )
            if include_title
            else None,
            center_title=False,
            bgcolor=ft.Colors.TRANSPARENT,
        )

    return None


@ft.component
def AppShell() -> Control:
    controller = ft.use_context(ControllerMethodsCtx)
    state = ft.use_context(AppStateCtx)

    active_tab, set_active_tab = ft.use_state(0)
    active_view, set_active_view = ft.use_state("dashboard")
    theme_ver, set_theme_ver = ft.use_state(state.theme_version)
    # Viewport width drives the chrome class (compact/medium/expanded).
    # Unknown at first paint → compact (bottom nav, the safe default).
    viewport_width, set_viewport_width = ft.use_state(None)

    # Wire navigation and theme closures
    controller.set_theme_mode = lambda _mode: set_theme_ver(state.theme_version)
    controller.go_home = lambda: (set_active_view("dashboard"), set_active_tab(0))
    controller.show_map = lambda: (set_active_view("dashboard"), set_active_tab(1))
    controller.show_space = lambda: set_active_view("space")
    controller.show_report = lambda: set_active_view("report")
    controller.show_settings = lambda: (
        set_active_view("dashboard"),
        set_active_tab(_TAB_INDEX["Settings"]),
    )
    controller.show_history = lambda: (
        set_active_view("dashboard"),
        set_active_tab(_TAB_INDEX["History"]),
    )
    controller.back = lambda: set_active_view("dashboard")
    controller.navigate_tab = lambda idx: (
        set_active_view("dashboard"),
        set_active_tab(idx),
    )

    def _on_tab_event(e):
        idx = e.control.selected_index
        logger.info("Navigated to tab '%s' (index %d)", _TAB_NAMES[idx], idx)
        set_active_view("dashboard")
        set_active_tab(idx)

    def _toggle_sidebar():
        collapsed = not state.sidebar_collapsed
        state.sidebar_collapsed = collapsed
        if controller.save_setting:
            from core.tasks import schedule

            schedule(
                controller.save_setting,
                STORAGE_SIDEBAR_COLLAPSED,
                "true" if collapsed else "false",
                page=flet_context.page,
            )

    def _sync_chrome():
        page = flet_context.page
        if not page or not page.views:
            return

        try:
            page.views[0].appbar = _build_appbar(
                active_view,
                active_tab,
                controller,
                include_title=window_class(viewport_width) == "compact",
            )
        except Exception:
            logger.exception("Suppressed exception")

        # Compact windows and overlay views keep the bottom bar contract:
        # dashboard tabs get NavigationBar, overlays hide it (back arrow
        # in the appbar is the way out). Medium/expanded windows render
        # rail/sidebar inline instead — navigation_bar stays None there.
        wclass = window_class(viewport_width)
        if active_view in ("report", "space") or wclass != "compact":
            page.views[0].navigation_bar = None
        else:
            page.views[0].navigation_bar = build_navigation_bar(
                active_tab, _on_tab_event
            )
        try:
            page.update()
        except Exception:
            logger.exception("Suppressed exception")

    def _track_viewport():
        page = flet_context.page
        if not page:
            return

        def _on_resize(e):
            try:
                set_viewport_width(e.width)
            except Exception:
                logger.exception("Suppressed exception")

        try:
            page.on_resize = _on_resize
        except Exception:
            logger.exception("Suppressed exception")

        # page.width is often None at first paint (Flet reports the viewport
        # after the session handshake) and on_resize may not fire afterwards
        # — poll briefly on the page loop until a real width arrives.
        async def _poll_width():
            import asyncio as _aio

            for _ in range(60):  # ~6s bounded
                w = getattr(page, "width", None)
                if w:
                    set_viewport_width(w)
                    return
                await _aio.sleep(0.1)
            set_viewport_width(getattr(page, "width", None))

        from core.tasks import schedule as _schedule

        _schedule(_poll_width, page=page)

    ft.use_effect(_track_viewport, [])
    ft.use_effect(
        _sync_chrome,
        [
            active_tab,
            active_view,
            theme_ver,
            viewport_width,
            state.theme_version,
        ],
    )

    # Ctrl+K / Cmd+K opens the command palette
    def _open_palette():
        from components.command_palette import show_command_palette

        _page = flet_context.page
        if _page:
            show_command_palette(_page, controller=controller)

    def _on_keyboard(e: ft.KeyboardEvent):
        if e.key == "k" and (e.ctrl or e.meta):
            _open_palette()

    _kb_page = flet_context.page
    if _kb_page:
        try:
            _kb_page.on_keyboard_event = _on_keyboard
        except Exception:
            logger.exception("Suppressed exception")

    # ── Branch Screen (Depends on state reactivity hooks) ──
    _ = (
        theme_ver,
        state.theme_version,
        state.telemetry_version,
        state.telemetry_version,
    )
    if active_view == "report":
        screen = ReportScreen()
    elif active_view == "space":
        screen = SpaceScreen()
    else:
        screen = resolve_dashboard_screen(active_tab)()

    wclass = window_class(viewport_width)
    use_side_chrome = active_view == "dashboard" and wclass in (
        "medium",
        "expanded",
    )

    screen_holder = ft.Container(
        content=screen,
        key=f"shell_screen_{active_tab}_{active_view}_{theme_ver}",
        expand=True,
    )
    if use_side_chrome:
        # Constrain content width on wide windows instead of full-bleed.
        # (Container has no max_width in 1.0.3 — pad symmetrically past the
        # cap so the column centers itself.)
        try:
            vw = float(viewport_width or 0)
        except (TypeError, ValueError):
            vw = 0.0
        side_w = (
            tokens.SIDEBAR_RAIL_WIDTH
            if state.sidebar_collapsed or wclass == "medium"
            else tokens.SIDEBAR_EXPANDED_WIDTH
        )
        gutter = max(0.0, (vw - side_w - tokens.CONTENT_MAX_WIDTH) / 2.0)
        screen_holder = ft.Container(
            content=screen_holder,
            expand=True,
            padding=ft.Padding(gutter, 0, gutter, 0),
        )

    if not use_side_chrome:
        return ft.SafeArea(content=screen_holder, expand=True)

    def _select_tab(idx: int):
        set_active_view("dashboard")
        set_active_tab(idx)

    side = (
        build_sidebar(
            active_tab,
            _select_tab,
            state.sidebar_collapsed,
            _toggle_sidebar,
        )
        if wclass == "expanded"
        else build_navigation_rail(active_tab, _on_tab_event)
    )
    kp_raw = state.space_weather.get("kp_index", "--")
    try:
        kp_text = f"Kp {float(kp_raw):.1f}"
    except (TypeError, ValueError):
        kp_text = "Kp --"

    # Per-screen header contents — absorbed from the old per-screen
    # AppHeader so screens render no chrome of their own. Report/space
    # overlays get a title here; dashboard tabs show live context.
    _SCREEN_TITLES = {
        "report": ("Location Risk Dossier", "MULTI-HAZARD RISK ASSESSMENT"),
        "space": ("Planetary Magnetosphere", "NOAA SPACE WEATHER PREDICTION"),
    }
    _TAB_TITLES = {
        0: ("Asase", "EARTH INTELLIGENCE"),
        1: ("Full Map", "PLANETARY HAZARD RADAR"),
        2: ("Planetary Magnetosphere", "NOAA SPACE WEATHER PREDICTION"),
        3: ("History", "SAVED LOCATIONS & RECENT SEARCHES"),
        4: ("Settings", "CONFIGURATION & DIAGNOSTICS"),
    }
    if active_view in _SCREEN_TITLES:
        _sb_title, _sb_subtitle = _SCREEN_TITLES[active_view]
    else:
        _sb_title, _sb_subtitle = _TAB_TITLES.get(active_tab, ("Asase", None))

    def _toggle_theme_mode():
        from core.tasks import schedule as _schedule

        _page = flet_context.page
        if not _page:
            return
        if _page.theme_mode == ft.ThemeMode.DARK:
            _page.theme_mode = ft.ThemeMode.LIGHT
            _mode_str = "light"
        elif _page.theme_mode == ft.ThemeMode.LIGHT:
            _page.theme_mode = ft.ThemeMode.SYSTEM
            _mode_str = "system"
        else:
            _page.theme_mode = ft.ThemeMode.DARK
            _mode_str = "dark"
        state.theme_mode = _page.theme_mode
        state.theme_version += 1
        state.telemetry_version += 1
        if controller.save_setting:
            _schedule(controller.save_setting, "asase.theme", _mode_str, page=_page)
        try:
            _page.update()
        except Exception:
            logger.exception("Suppressed exception")

    def _theme_icon():
        _page = flet_context.page
        if not _page or _page.theme_mode == ft.ThemeMode.DARK:
            return ft.Icons.DARK_MODE_ROUNDED
        if _page and _page.theme_mode == ft.ThemeMode.LIGHT:
            return ft.Icons.LIGHT_MODE_ROUNDED
        return ft.Icons.BRIGHTNESS_AUTO_ROUNDED

    def _theme_tooltip():
        # CollabShell pattern: the tooltip reflects the CURRENT mode, so the
        # button reads as a state indicator, not an ambiguous cycler.
        _page = flet_context.page
        if not _page or _page.theme_mode == ft.ThemeMode.DARK:
            return "Dark Theme"
        if _page and _page.theme_mode == ft.ThemeMode.LIGHT:
            return "Light Theme"
        return "System Theme"

    def _open_version_dialog():
        open_version_dialog(flet_context.page)

    def _refresh_feeds():
        # refresh_all is async — the status bar invokes on_refresh as a
        # plain sync callback, so it must be scheduled, never bare-called.
        from core.tasks import schedule

        schedule(controller.refresh_all, page=flet_context.page)

    def _open_command_palette():
        from components.command_palette import show_command_palette as _show

        _show(flet_context.page, controller=controller)

    _update_data = state.update_data or {}
    status = build_status_bar(
        state.current_location_name,
        len(state.earthquakes) + len(state.disasters),
        kp_text,
        _open_command_palette,
        is_dark=is_dark_mode(flet_context.page),
        title=_sb_title,
        subtitle=_sb_subtitle,
        on_refresh=_refresh_feeds,
        on_settings=lambda: _select_tab(_TAB_INDEX["Settings"]),
        on_toggle_theme=_toggle_theme_mode,
        theme_icon=_theme_icon(),
        theme_tooltip=_theme_tooltip(),
        on_open_version=_open_version_dialog,
        version_label=(
            f"Update: {(_update_data.get('version', 'Update'))} Available!"
            if state.update_available and _update_data.get("type") != "announcement"
            else ("News" if state.update_available else f"v{APP_VERSION}")
        ),
        update_available=bool(state.update_available),
    )
    body = ft.Row(
        [side, ft.Column([status, screen_holder], spacing=0, expand=True)],
        spacing=0,
        expand=True,
    )
    return ft.SafeArea(content=body, expand=True)
