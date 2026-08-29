"""SettingsScreen — Telemetry parameters, theme switching, and diagnostics terminal."""

from __future__ import annotations

import asyncio
import logging

import flet as ft
from flet import Control

from components.app_header import build_app_header
from components.banner_ad import build_banner_ad
from components.section_header import SectionHeader
from components.settings.sections_about import build_about_card, build_terminal_card
from components.settings.sections_hazards import build_hazards_section
from components.settings.sections_theme import build_theme_section
from components.settings.sections_units import build_units_section
from core import tokens
from core.constants import (
    STORAGE_MIN_MAGNITUDE,
    STORAGE_SPEED_UNIT,
    STORAGE_TEMP_UNIT,
    STORAGE_THEME,
)
from core.notify import show_snack
from core.theme import AppColors
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.settings")


@ft.component
def SettingsScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    from flet import context as flet_context

    page = flet_context.page

    def _current_theme_str() -> str:
        if not page or page.theme_mode == ft.ThemeMode.DARK:
            return "dark"
        if page.theme_mode == ft.ThemeMode.LIGHT:
            return "light"
        return "system"

    async def _on_theme_change(val: str):
        if not page:
            return
        if val == "system":
            new_mode = ft.ThemeMode.SYSTEM
        elif val == "light":
            new_mode = ft.ThemeMode.LIGHT
        else:
            new_mode = ft.ThemeMode.DARK
        page.theme_mode = new_mode
        state.theme_mode = new_mode
        state.theme_version += 1
        state.telemetry_version += 1
        if controller.save_setting:
            await controller.save_setting(STORAGE_THEME, val)
        page.update()

    def _on_magnitude_change(val: str):
        try:
            m = float(val)
            state.min_magnitude_filter = m
            if controller.save_setting:
                asyncio.create_task(controller.save_setting(STORAGE_MIN_MAGNITUDE, m))
            if controller.refresh_all:
                asyncio.create_task(controller.refresh_all())
        except Exception:
            pass

    def _on_temp_unit_change(val: str):
        state.temp_unit = val.lower()
        if controller.save_setting:
            asyncio.create_task(
                controller.save_setting(STORAGE_TEMP_UNIT, state.temp_unit)
            )

    def _on_speed_unit_change(val: str):
        state.speed_unit = val.lower()
        if controller.save_setting:
            asyncio.create_task(
                controller.save_setting(STORAGE_SPEED_UNIT, state.speed_unit)
            )

    def _clear_history_dialog():
        if not page:
            return

        def _do_clear():
            state.recent_searches.clear()
            if controller.save_setting:
                asyncio.create_task(
                    controller.save_setting("asase.recent_searches", [])
                )
            page.pop_dialog()
            show_snack(page, "Search history cleared", bgcolor=AppColors.SUCCESS)

        dlg = ft.AlertDialog(
            title=ft.Text("Clear Search History?"),
            content=ft.Text("This will remove all recent location queries."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: page.pop_dialog()),
                ft.FilledButton(
                    "Clear All",
                    on_click=lambda _: _do_clear(),
                    style=ft.ButtonStyle(bgcolor=AppColors.ERROR),
                ),
            ],
        )
        page.show_dialog(dlg)

    # Sub-component cards
    theme_card = build_theme_section(page, _current_theme_str(), _on_theme_change)
    units_card = build_units_section(
        state.temp_unit, state.speed_unit, _on_temp_unit_change, _on_speed_unit_change
    )
    telemetry_card, storage_card = build_hazards_section(
        state.min_magnitude_filter, _on_magnitude_change, _clear_history_dialog
    )
    terminal_card = build_terminal_card(page)
    about_card = build_about_card(page)

    header_view = build_app_header(
        page,
        title="Settings",
        subtitle="CONFIGURATION & DIAGNOSTICS",
        on_refresh=controller.refresh_all,
        save_setting_fn=controller.save_setting,
    )

    return ft.ListView(
        controls=[
            header_view,
            ft.Container(height=tokens.SPACE_SM),
            SectionHeader("DISPLAY THEME"),
            ft.Container(
                content=theme_card,
                padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
            ),
            ft.Container(height=tokens.SPACE_MD),
            SectionHeader("MEASUREMENT UNITS"),
            ft.Container(
                content=units_card,
                padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
            ),
            ft.Container(height=tokens.SPACE_MD),
            SectionHeader("PLANETARY TELEMETRY THRESHOLDS"),
            ft.Container(
                content=telemetry_card,
                padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
            ),
            ft.Container(height=tokens.SPACE_MD),
            SectionHeader("STORAGE & CACHE"),
            ft.Container(
                content=storage_card,
                padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
            ),
            ft.Container(height=tokens.SPACE_MD),
            SectionHeader("SYSTEM DIAGNOSTICS"),
            ft.Container(
                content=terminal_card,
                padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
            ),
            ft.Container(height=tokens.SPACE_MD),
            SectionHeader("ABOUT ASASE"),
            ft.Container(
                content=about_card,
                padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
            ),
            ft.Container(height=tokens.SPACE_LG),
            build_banner_ad(page),
            ft.Container(height=tokens.SPACE_XL),
        ],
        spacing=0,
        expand=True,
    )
