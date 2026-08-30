"""Hazard category filter chips — DDGS _category_chip pattern for Asase."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors, is_dark_mode

CHIP_OPTIONS: list[tuple[str, str, ft.IconData]] = [
    ("all", "All", ft.Icons.PUBLIC_ROUNDED),
    ("earthquake", "Seismic", ft.Icons.VIBRATION_ROUNDED),
    ("wildfire", "Wildfire", ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED),
    ("flood", "Flood", ft.Icons.WATER_DROP_ROUNDED),
    ("storm", "Storm", ft.Icons.CYCLONE_ROUNDED),
    ("volcano", "Volcano", ft.Icons.VOLCANO_ROUNDED),
]


def _chip(
    key: str,
    label: str,
    icon: ft.IconData,
    selected: bool,
    on_tap: Callable[[str], None],
    page: ft.Page | None,
) -> ft.Control:
    dark = is_dark_mode(page)
    bg = (
        AppColors.PRIMARY
        if selected
        else (AppColors.DARK_SURFACE_2 if dark else ft.Colors.WHITE)
    )
    fg = (
        ft.Colors.WHITE
        if selected
        else (AppColors.DARK_MUTED if dark else AppColors.LIGHT_MUTED)
    )
    border_c = AppColors.PRIMARY if selected else AppColors.get_border(page)
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(
                    icon,
                    size=14,
                    color=AppColors.PRIMARY if not selected else ft.Colors.WHITE,
                ),
                ft.Text(
                    label,
                    size=tokens.FONT_XS,
                    weight=ft.FontWeight.W_600,
                    color=fg if not selected else ft.Colors.WHITE,
                ),
            ],
            spacing=4,
            tight=True,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        padding=ft.Padding(10, 6, 10, 6),
        border_radius=tokens.RADIUS_FULL,
        bgcolor=bg,
        border=ft.Border.all(1, border_c),
        on_click=lambda _: on_tap(key),
        ink=True,
    )


def build_hazard_filter_chips(
    page: ft.Page | None,
    selected: str,
    on_select: Callable[[str], None],
) -> ft.Control:
    chips = [
        _chip(k, lbl, ic, selected == k, on_select, page) for k, lbl, ic in CHIP_OPTIONS
    ]
    return ft.Container(
        content=ft.Row(
            chips, spacing=tokens.SPACE_XS, scroll=ft.ScrollMode.AUTO, wrap=False
        ),
        padding=ft.Padding(tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0),
    )
