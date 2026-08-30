"""AppShell — Top-level shell managing tabs, sub-views, and chrome sync."""

from __future__ import annotations

import logging

import flet as ft
from flet import Control

from core import tokens
from core.theme import AppColors
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
    controller.show_settings = lambda: (set_active_view("dashboard"), set_active_tab(3))
    controller.show_history = lambda: (set_active_view("dashboard"), set_active_tab(4))
    controller.back = lambda: set_active_view("dashboard")
    controller.navigate_tab = lambda idx: set_active_tab(idx)

    from flet import context as flet_context

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

        if active_view in ("report", "space"):
            page.views[0].navigation_bar = None
            try:
                page.update()
            except Exception:
                pass
            return

        # Dashboard / Tabs
        destinations = [
            ft.NavigationBarDestination(icon=icon, label=label)
            for icon, label in zip(_TAB_ICONS, _TAB_NAMES, strict=True)
        ]

        def _on_tab_change(e):
            idx = e.control.selected_index
            logger.info("Navigated to tab '%s' (index %d)", _TAB_NAMES[idx], idx)
            set_active_tab(idx)

        page.views[0].navigation_bar = ft.NavigationBar(
            destinations=destinations,
            selected_index=active_tab,
            on_change=_on_tab_change,
            indicator_color=ft.Colors.with_opacity(0.2, AppColors.PRIMARY),
        )
        try:
            page.update()
        except Exception:
            pass

    ft.use_effect(
        _sync_chrome,
        [
            active_tab,
            active_view,
            onboarding_done,
            theme_ver,
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
        if active_tab == 0:
            screen = HomeScreen()
        elif active_tab == 1:
            screen = MapScreen()
        elif active_tab == 2:
            screen = SpaceScreen()
        elif active_tab == 3:
            from screens.history_screen import HistoryScreen

            screen = HistoryScreen()
        else:
            screen = SettingsScreen()

    return ft.SafeArea(
        content=ft.Container(
            content=screen,
            key=f"shell_screen_{active_tab}_{active_view}_{theme_ver}",
            expand=True,
        ),
        expand=True,
    )
