"""Home location search bar and suggestions overlay."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors


def build_location_search_bar(
    page: ft.Page,
    search_query: str,
    search_results: list[dict],
    on_search_change: Callable,
    on_select_city: Callable,
    on_locate_gps: Callable,
) -> ft.Container:
    """Builds the modern Material 3 SearchBar with adaptive surfaces and suggestions."""
    suggestions = [
        ft.ListTile(
            leading=ft.Icon(
                ft.Icons.LOCATION_CITY_ROUNDED,
                color=AppColors.PRIMARY,
                size=tokens.ICON_MD,
            ),
            title=ft.Text(
                f"{c['name']}, {c.get('country', '')}",
                weight=ft.FontWeight.W_600,
                size=tokens.FONT_SM,
                font_family="Outfit",
            ),
            subtitle=ft.Text(
                f"Elevation: {int(c.get('elevation', 0))}m • Lat: {c.get('latitude', 0.0):.2f}°, Lon: {c.get('longitude', 0.0):.2f}°",
                size=tokens.FONT_XS,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            on_click=lambda _, city=c: on_select_city(city),
        )
        for c in search_results
    ]

    return ft.Container(
        content=ft.SearchBar(
            value=search_query,
            bar_hint_text="Search city, coordinates, or region...",
            bar_leading=ft.Icon(
                ft.Icons.SEARCH_ROUNDED,
                color=AppColors.PRIMARY,
            ),
            bar_trailing=[
                ft.IconButton(
                    icon=ft.Icons.MY_LOCATION_ROUNDED,
                    tooltip="Locate via GPS",
                    icon_color=AppColors.PRIMARY,
                    on_click=lambda _: (
                        asyncio.create_task(on_locate_gps()) if on_locate_gps else None
                    ),
                ),
            ],
            bar_bgcolor=AppColors.get_surface(page),
            bar_border_side=ft.BorderSide(1, AppColors.get_border(page)),
            bar_shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD),
            bar_text_style=ft.TextStyle(
                size=tokens.FONT_SM,
                weight=ft.FontWeight.W_500,
                font_family="Outfit",
            ),
            bar_hint_text_style=ft.TextStyle(
                size=tokens.FONT_SM,
                weight=ft.FontWeight.W_400,
                color=ft.Colors.ON_SURFACE_VARIANT,
                font_family="Outfit",
            ),
            controls=suggestions,
            on_change=on_search_change,
            on_submit=lambda e: on_search_change(e),
        ),
        padding=ft.Padding(tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0),
    )
