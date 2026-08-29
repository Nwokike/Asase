"""Settings display theme section."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors


def build_theme_section(
    page: ft.Page, current_theme: str, change_theme_fn: Callable
) -> ft.Container:
    """Builds a 3-way segmented color mode card (Light / Dark / System) matching DDGS."""

    def create_theme_card(mode: str, label: str, icon: ft.IconData):
        is_sel = current_theme == mode
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        icon,
                        color=(
                            AppColors.PRIMARY
                            if is_sel
                            else ft.Colors.ON_SURFACE_VARIANT
                        ),
                        size=tokens.ICON_MD,
                    ),
                    ft.Text(
                        label,
                        size=tokens.FONT_SM,
                        weight=ft.FontWeight.W_600 if is_sel else ft.FontWeight.NORMAL,
                        color=AppColors.PRIMARY if is_sel else ft.Colors.ON_SURFACE,
                        font_family="Outfit",
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=tokens.SPACE_XS,
            ),
            padding=ft.Padding(
                tokens.SPACE_MD, tokens.SPACE_SM, tokens.SPACE_MD, tokens.SPACE_SM
            ),
            border_radius=tokens.RADIUS_MD,
            border=(
                ft.Border.all(2, AppColors.PRIMARY)
                if is_sel
                else ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE))
            ),
            bgcolor=(
                ft.Colors.with_opacity(0.12, AppColors.PRIMARY)
                if is_sel
                else ft.Colors.with_opacity(0.04, ft.Colors.ON_SURFACE)
            ),
            expand=True,
            animate=ft.Animation(tokens.ANIM_FAST, "easeOut"),
            on_click=lambda _: asyncio.create_task(change_theme_fn(mode)),
        )

    light_btn = create_theme_card("light", "Light", ft.Icons.LIGHT_MODE_ROUNDED)
    dark_btn = create_theme_card("dark", "Dark", ft.Icons.DARK_MODE_ROUNDED)
    system_btn = create_theme_card(
        "system", "System", ft.Icons.SETTINGS_SYSTEM_DAYDREAM_ROUNDED
    )

    return ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.COLOR_LENS_ROUNDED,
                            color=AppColors.PRIMARY,
                            size=tokens.ICON_SM,
                        ),
                        ft.Text(
                            "Display Theme",
                            size=tokens.FONT_MD,
                            weight=ft.FontWeight.W_600,
                            font_family="Outfit",
                        ),
                    ],
                    spacing=tokens.SPACE_SM,
                ),
                ft.Divider(
                    height=1,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
                ),
                ft.Row(
                    [light_btn, dark_btn, system_btn],
                    spacing=tokens.SPACE_SM,
                ),
            ],
            spacing=tokens.SPACE_SM,
        ),
        padding=tokens.SPACE_MD,
    )
