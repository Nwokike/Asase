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
from core.constants import STORAGE_SIDEBAR_COLLAPSED
from core.theme import is_dark_mode
from screens.home_screen import HomeScreen
from screens.map_screen import MapScreen
from screens.onboarding_screen import OnboardingScreen
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


def _should_show_onboarding(state) -> bool:
    return state.is_first_launch or not state.has_accepted_terms


def _build_appbar(active_view: str, active_tab: int, controller) -> ft.AppBar | None:
    if active_view == "report":
        return ft.AppBar(
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_ROUNDED,
                on_click=lambda _: controller.go_home() if controller.go_home else None,
            ),
            title=ft.Text(
                "Location Risk Dossier", size=tokens.FONT_LG, weight=ft.FontWeight.W_600
            ),
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
            ),
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
    onboarding_done, set_onboarding_done = ft.use_state(state.has_accepted_terms)
    # Viewport width drives the chrome class (compact/medium/expanded).
    # Unknown at first paint → compact (bottom nav, the safe default).
    viewport_width, set_viewport_width = ft.use_state(None)

    # Wire navigation and theme closures
    controller.set_theme_mode = lambda _mode: set_theme_ver(state.theme_version)
    controller.dismiss_onboarding = lambda: (
        set_onboarding_done(True),
        set_active_view("dashboard"),
        set_active_tab(0),
    )
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
            page.views[0].appbar = _build_appbar(active_view, active_tab, controller)
        except Exception:
            pass

        show_onboarding = not onboarding_done and _should_show_onboarding(state)
        if show_onboarding:
            page.views[0].navigation_bar = None
            try:
                page.update()
            except Exception:
                pass
            return

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
            pass

    def _track_viewport():
        page = flet_context.page
        if not page:
            return
        try:
            set_viewport_width(page.width)
        except Exception:
            pass

        def _on_resize(e):
            try:
                set_viewport_width(e.width)
            except Exception:
                pass

        try:
            page.on_resize = _on_resize
        except Exception:
            pass

    ft.use_effect(_track_viewport, [])
    ft.use_effect(
        _sync_chrome,
        [
            active_tab,
            active_view,
            onboarding_done,
            theme_ver,
            viewport_width,
            state.has_accepted_terms,
            state.theme_version,
        ],
    )

    # ── Branch Screen (Depends on state reactivity hooks) ──
    _ = (
        theme_ver,
        state.theme_version,
        state.telemetry_version,
        state.has_accepted_terms,
    )
    if not onboarding_done and _should_show_onboarding(state):
        screen = OnboardingScreen()
    elif active_view == "report":
        screen = ReportScreen()
    elif active_view == "space":
        screen = SpaceScreen()
    else:
        screen = resolve_dashboard_screen(active_tab)()

    show_onboarding_now = not onboarding_done and _should_show_onboarding(state)
    wclass = window_class(viewport_width)
    use_side_chrome = (
        not show_onboarding_now
        and active_view == "dashboard"
        and wclass in ("medium", "expanded")
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
    status = build_status_bar(
        state.current_location_name,
        len(state.earthquakes) + len(state.disasters),
        kp_text,
        lambda: None,  # command palette lands in Phase D4
        is_dark=is_dark_mode(flet_context.page),
    )
    body = ft.Row(
        [side, ft.Column([status, screen_holder], spacing=0, expand=True)],
        spacing=0,
        expand=True,
    )
    return ft.SafeArea(content=body, expand=True)
