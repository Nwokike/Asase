"""Unified Branded AppHeader with Adaptive SVG Icon & Color Mode Switcher."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors, is_dark_mode


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
    # When title is the brand name "Asase", render the full logo SVG directly (which
    # already contains the wordmark "Asase" + "Earth Intelligence") without repeating
    # redundant text. For other screens (e.g. Settings, Space), render icon.svg + title.
    if title == "Asase":
        branding = ft.Image(
            src="/logo.svg",
            height=32,
            fit=ft.BoxFit.CONTAIN,
        )
    else:
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

    # Right: Action Icons
    actions = [
        ft.IconButton(
            icon=_get_theme_icon(),
            icon_size=20,
            tooltip="Toggle Color Mode (Dark / Light / System)",
            on_click=_toggle_theme,
        )
    ]

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
