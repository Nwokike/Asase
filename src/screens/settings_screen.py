"""SettingsScreen — Telemetry parameters, theme, and diagnostics terminal.

Follows the Sherlock & KTV Player structured card layout.
"""

from __future__ import annotations

import asyncio
import logging

import flet as ft
from flet import Control

from components.activity_terminal import show_activity_terminal_dialog
from components.banner_ad import build_banner_ad
from components.section_header import SectionHeader
from core import tokens
from core.constants import (
    APP_NAME,
    APP_SUBTITLE,
    APP_VERSION,
    STORAGE_MIN_MAGNITUDE,
    STORAGE_SPEED_UNIT,
    STORAGE_TEMP_UNIT,
    STORAGE_THEME,
)
from core.notify import show_snack
from core.theme import (
    AppColors,
    AppStyles,
)
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.settings")


def _setting_row(
    icon: ft.IconData,
    title: str,
    subtitle: str,
    trailing: Control,
) -> ft.Container:
    """Reusable settings row."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(
                        icon,
                        size=tokens.ICON_MD,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    width=tokens.ICON_BACKDROP,
                    height=tokens.ICON_BACKDROP,
                    border_radius=tokens.ICON_BACKDROP_RADIUS,
                    bgcolor=ft.Colors.with_opacity(
                        tokens.OPACITY_LIGHT, ft.Colors.ON_SURFACE
                    ),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(title, size=tokens.FONT_MD, weight=ft.FontWeight.W_500),
                        ft.Text(
                            subtitle,
                            size=tokens.FONT_XS,
                            color=ft.Colors.with_opacity(
                                tokens.OPACITY_DIM, ft.Colors.ON_SURFACE
                            ),
                        ),
                    ],
                    spacing=tokens.SPACE_XXS,
                    expand=True,
                ),
                trailing,
            ],
            spacing=tokens.SPACE_MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(
            left=tokens.SPACE_LG,
            right=tokens.SPACE_LG,
            top=tokens.SPACE_MD,
            bottom=tokens.SPACE_MD,
        ),
    )


@ft.component
def SettingsScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    from flet import context as flet_context

    def _get_page():
        return flet_context.page

    page = _get_page()

    async def _on_theme_change(val: str):
        if val == "system":
            new_mode = ft.ThemeMode.SYSTEM
        elif val == "light":
            new_mode = ft.ThemeMode.LIGHT
        else:
            new_mode = ft.ThemeMode.DARK
        page.theme_mode = new_mode
        state.theme_mode = new_mode
        if controller.save_setting:
            await controller.save_setting(STORAGE_THEME, val)

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

    # ── Cards ──

    # Preferences
    preferences_card = AppStyles.glass_card(
        ft.Column(
            [
                _setting_row(
                    ft.Icons.COLOR_LENS_ROUNDED,
                    "Theme Mode",
                    "Choose between System, Dark, or Light",
                    ft.Dropdown(
                        value=(
                            state.theme_mode.value.capitalize()
                            if isinstance(state.theme_mode, ft.ThemeMode)
                            else "System"
                        ),
                        options=[
                            ft.DropdownOption("System", "System"),
                            ft.DropdownOption("Dark", "Dark"),
                            ft.DropdownOption("Light", "Light"),
                        ],
                        width=110,
                        height=44,
                        text_size=tokens.FONT_SM,
                        border_radius=tokens.RADIUS_SM,
                        focused_border_color=AppColors.PRIMARY,
                        on_select=lambda e: asyncio.create_task(
                            _on_theme_change(e.control.value)
                        ),
                    ),
                ),
                ft.Divider(
                    height=1,
                    color=ft.Colors.with_opacity(
                        tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                    ),
                ),
                _setting_row(
                    ft.Icons.THERMOSTAT_ROUNDED,
                    "Temperature Unit",
                    "Choose Celsius (°C) or Fahrenheit (°F)",
                    ft.Dropdown(
                        value="Celsius"
                        if state.temp_unit == "celsius"
                        else "Fahrenheit",
                        options=[
                            ft.DropdownOption("Celsius", "Celsius (°C)"),
                            ft.DropdownOption("Fahrenheit", "Fahrenheit (°F)"),
                        ],
                        width=140,
                        height=44,
                        text_size=tokens.FONT_SM,
                        border_radius=tokens.RADIUS_SM,
                        on_select=lambda e: _on_temp_unit_change(e.control.value),
                    ),
                ),
            ],
            spacing=0,
        ),
        padding=0,
    )

    # Telemetry Thresholds
    telemetry_card = AppStyles.glass_card(
        ft.Column(
            [
                _setting_row(
                    ft.Icons.PULSE_ALERT_ROUNDED,
                    "Min Seismic Magnitude",
                    "Filter out minor tremors below this Richter scale threshold",
                    ft.Dropdown(
                        value=f"{state.min_magnitude_filter:.1f}",
                        options=[
                            ft.DropdownOption("1.0", "M1.0+ (Micro)"),
                            ft.DropdownOption("2.5", "M2.5+ (Minor)"),
                            ft.DropdownOption("4.5", "M4.5+ (Moderate)"),
                            ft.DropdownOption("6.0", "M6.0+ (Major)"),
                        ],
                        width=140,
                        height=44,
                        text_size=tokens.FONT_SM,
                        border_radius=tokens.RADIUS_SM,
                        on_select=lambda e: _on_magnitude_change(e.control.value),
                    ),
                ),
            ],
            spacing=0,
        ),
        padding=0,
    )

    # Activity Terminal
    terminal_card = AppStyles.glass_card(
        ft.Column(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.TERMINAL_ROUNDED,
                                    size=tokens.ICON_MD,
                                    color=AppColors.PRIMARY,
                                ),
                                width=tokens.ICON_BACKDROP,
                                height=tokens.ICON_BACKDROP,
                                border_radius=tokens.ICON_BACKDROP_RADIUS,
                                bgcolor=ft.Colors.with_opacity(
                                    tokens.OPACITY_LIGHT, AppColors.PRIMARY
                                ),
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Live Activity Terminal",
                                        size=tokens.FONT_MD,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    ft.Text(
                                        "Stream real-time API logs, connection events, and raw telemetry.",
                                        size=tokens.FONT_XS,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                                spacing=tokens.SPACE_XXS,
                                expand=True,
                            ),
                            ft.FilledButton(
                                "Open Log",
                                icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                                style=ft.ButtonStyle(
                                    bgcolor=AppColors.PRIMARY,
                                    shape=ft.RoundedRectangleBorder(
                                        radius=tokens.RADIUS_MD
                                    ),
                                ),
                                on_click=lambda _: show_activity_terminal_dialog(page),
                            ),
                        ],
                        spacing=tokens.SPACE_MD,
                    ),
                    padding=tokens.SPACE_MD,
                ),
            ],
            spacing=0,
        ),
        padding=0,
    )

    # Storage & History
    storage_card = AppStyles.glass_card(
        ft.Column(
            [
                _setting_row(
                    ft.Icons.DELETE_SWEEP_ROUNDED,
                    "Clear Search History",
                    "Delete all saved recent search locations",
                    ft.OutlinedButton(
                        "Clear",
                        style=ft.ButtonStyle(color=AppColors.ERROR),
                        on_click=lambda _: _clear_history_dialog(),
                    ),
                ),
            ],
            spacing=0,
        ),
        padding=0,
    )

    # About
    about_card = AppStyles.glass_card(
        ft.Container(
            content=ft.Column(
                [
                    ft.Image(
                        src="icon.png",
                        width=48,
                        height=48,
                        border_radius=tokens.RADIUS_MD,
                    ),
                    ft.Container(height=tokens.SPACE_XS),
                    ft.Text(APP_NAME, size=tokens.FONT_LG, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        f"Version {APP_VERSION}",
                        size=tokens.FONT_SM,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Container(height=tokens.SPACE_XS),
                    ft.Text(
                        APP_SUBTITLE,
                        size=tokens.FONT_SM,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Powered by Open-Meteo, USGS, NASA EONET & NOAA SWPC.\n100% Free & Open Public Domain Planetary Telemetry.",
                        size=tokens.FONT_XS,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_DIM, ft.Colors.ON_SURFACE
                        ),
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=tokens.SPACE_XXS,
            ),
            padding=tokens.SPACE_LG,
            alignment=ft.Alignment.CENTER,
        ),
        padding=0,
    )

    return ft.ListView(
        controls=[
            ft.Container(height=tokens.SPACE_SM),
            SectionHeader("PREFERENCES"),
            ft.Container(
                content=preferences_card,
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            SectionHeader("TELEMETRY THRESHOLDS"),
            ft.Container(
                content=telemetry_card,
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            build_banner_ad(page),
            SectionHeader("DIAGNOSTICS & TERMINAL"),
            ft.Container(
                content=terminal_card,
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            SectionHeader("STORAGE & CACHE"),
            ft.Container(
                content=storage_card,
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            SectionHeader("ABOUT"),
            ft.Container(
                content=about_card,
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            build_banner_ad(page),
            ft.Container(height=tokens.SPACE_XXXL),
        ],
        spacing=0,
        expand=True,
    )
