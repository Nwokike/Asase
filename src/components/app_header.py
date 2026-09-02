"""Unified Branded AppHeader with Adaptive SVG Icon & Color Mode Switcher."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from core import tokens
from core.constants import APP_VERSION
from core.state import state as core_state
from core.theme import AppColors, is_dark_mode


def _build_version_chip(page: ft.Page) -> ft.Control:
    """KTV-style version chip: shows the current version normally, flips to
    an Update pill when a newer build is found. Always opens the version
    dialog (changelog when up to date)."""

    def _open_dialog(e=None):
        from components.version_dialog import show_version_dialog

        show_version_dialog(page)

    if core_state.update_available:
        update_data = core_state.update_data or {}
        label = (
            update_data.get("version", "Update")
            if update_data.get("type") != "announcement"
            else "News"
        )
        content = ft.Row(
            controls=[
                ft.Text(
                    f"Update: {label} Available!"
                    if update_data.get("type") != "announcement"
                    else "News",
                    size=11,
                    weight=ft.FontWeight.BOLD,
                    color=AppColors.PRIMARY,
                    no_wrap=True,
                ),
                ft.Container(
                    width=6,
                    height=6,
                    border_radius=3,
                    bgcolor=AppColors.PRIMARY,
                ),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )
        return ft.Container(
            content=content,
            padding=ft.Padding(10, 4, 10, 4),
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.15, AppColors.PRIMARY),
            border=ft.Border.all(1.5, AppColors.PRIMARY),
            ink=True,
            tooltip="New update available — tap to view",
            on_click=lambda e: _open_dialog(),
        )
    return ft.Container(
        content=ft.Text(
            f"v{APP_VERSION}",
            size=11,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.ON_SURFACE_VARIANT,
            no_wrap=True,
        ),
        padding=ft.Padding(10, 4, 10, 4),
        border_radius=10,
        bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE_VARIANT),
        ink=True,
        tooltip="What's New — version & changelog",
        on_click=lambda e: _open_dialog(),
    )


def build_app_header(
    page: ft.Page,
    title: str = "Asase",
    subtitle: str = "EARTH INTELLIGENCE",
    on_refresh: Callable | None = None,
    on_settings: Callable | None = None,
    save_setting_fn: Callable | None = None,
) -> ft.Container:
    """Builds a standardized top header bar with transparent adaptive SVG icon and theme switcher."""
    is_dark = is_dark_mode(page)

    def _toggle_theme(e):
        if not page:
            return
        from core.state import state

        if page.theme_mode == ft.ThemeMode.DARK:
            page.theme_mode = ft.ThemeMode.LIGHT
            mode_str = "light"
        elif page.theme_mode == ft.ThemeMode.LIGHT:
            page.theme_mode = ft.ThemeMode.SYSTEM
            mode_str = "system"
        else:
            page.theme_mode = ft.ThemeMode.DARK
            mode_str = "dark"

        state.theme_mode = page.theme_mode
        state.theme_version += 1
        state.telemetry_version += 1

        if save_setting_fn:
            asyncio.create_task(save_setting_fn("asase.theme", mode_str))
        page.update()

    def _get_theme_icon() -> ft.IconData:
        if not page or page.theme_mode == ft.ThemeMode.DARK:
            return ft.Icons.DARK_MODE_ROUNDED
        if page.theme_mode == ft.ThemeMode.LIGHT:
            return ft.Icons.LIGHT_MODE_ROUNDED
        return ft.Icons.SETTINGS_SYSTEM_DAYDREAM_ROUNDED

    # Left: Clean Transparent Adaptive SVG Branding (no container padding or filler color)
    # Consistent on every screen: icon.svg tinted white in dark mode + screen title.
    branding = ft.Row(
        [
            ft.Image(
                src="/icon.svg",
                width=32,
                height=32,
                color=ft.Colors.WHITE if is_dark else None,
            ),
            ft.Column(
                [
                    ft.Text(
                        title,
                        size=tokens.FONT_MD,
                        weight=ft.FontWeight.BOLD,
                        font_family="Outfit",
                    ),
                    ft.Text(
                        subtitle.upper(),
                        size=8,
                        weight=ft.FontWeight.W_700,
                        color=AppColors.PRIMARY,
                    ),
                ],
                spacing=0,
            ),
        ],
        spacing=tokens.SPACE_SM,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # Right: Version chip + Action Icons
    actions = [_build_version_chip(page)]

    actions.append(
        ft.IconButton(
            icon=_get_theme_icon(),
            icon_size=20,
            tooltip="Toggle Color Mode (Dark / Light / System)",
            on_click=_toggle_theme,
        )
    )

    if on_refresh:
        actions.append(
            ft.IconButton(
                icon=ft.Icons.REFRESH_ROUNDED,
                icon_size=20,
                tooltip="Sync Live Feeds",
                on_click=lambda _: asyncio.create_task(on_refresh()),
            )
        )

    if on_settings:
        actions.append(
            ft.IconButton(
                icon=ft.Icons.SETTINGS_OUTLINED,
                icon_size=20,
                tooltip="Settings",
                on_click=lambda _: on_settings(),
            )
        )

    return ft.Container(
        content=ft.Row(
            [branding, ft.Row(actions, spacing=0)],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0),
    )
