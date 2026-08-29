"""Home location search bar and suggestions overlay."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors, is_dark_mode


def build_location_search_bar(
    page: ft.Page,
    search_query: str,
    search_results: list[dict],
    on_search_change: Callable,
    on_select_city: Callable,
    on_locate_gps: Callable,
) -> ft.Container:
    """Builds the reactive search bar and suggestions popup list with adaptive theme surfaces."""
    is_dark = is_dark_mode(page)

    return ft.Container(
        content=ft.Column(
            [
                ft.TextField(
                    value=search_query,
                    hint_text="Search city, region, or coordinates...",
                    prefix_icon=ft.Icons.SEARCH_ROUNDED,
                    suffix=ft.IconButton(
                        icon=ft.Icons.MY_LOCATION_ROUNDED,
                        tooltip="Locate via GPS",
                        icon_color=AppColors.PRIMARY,
                        on_click=lambda _: (
                            asyncio.create_task(on_locate_gps())
                            if on_locate_gps
                            else None
                        ),
                    ),
                    border_radius=tokens.RADIUS_MD,
                    filled=True,
                    bgcolor=(
                        ft.Colors.with_opacity(0.08, ft.Colors.WHITE)
                        if is_dark
                        else ft.Colors.with_opacity(0.06, ft.Colors.BLACK)
                    ),
                    border_color=ft.Colors.with_opacity(0.15, ft.Colors.OUTLINE),
                    on_change=on_search_change,
                    dense=True,
                ),
                *(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(
                                            ft.Icons.LOCATION_CITY_ROUNDED,
                                            color=AppColors.PRIMARY,
                                        ),
                                        title=ft.Text(
                                            f"{c['name']}, {c.get('country', '')}",
                                            weight=ft.FontWeight.W_600,
                                        ),
                                        subtitle=ft.Text(
                                            f"Elevation: {int(c.get('elevation', 0))}m • {c.get('timezone', 'UTC')}",
                                            size=tokens.FONT_XS,
                                        ),
                                        on_click=lambda _, city=c: on_select_city(city),
                                    )
                                    for c in search_results
                                ],
                                spacing=0,
                            ),
                            bgcolor=AppColors.get_surface(page),
                            border_radius=tokens.RADIUS_MD,
                            border=ft.Border.all(
                                1,
                                AppColors.get_border(page),
                            ),
                            shadow=ft.BoxShadow(
                                spread_radius=1,
                                blur_radius=8,
                                color=ft.Colors.with_opacity(0.15, ft.Colors.BLACK),
                            ),
                        )
                    ]
                    if search_results
                    else []
                ),
            ],
            spacing=tokens.SPACE_XS,
        ),
        padding=ft.Padding(tokens.SPACE_LG, tokens.SPACE_MD, tokens.SPACE_LG, 0),
    )
