"""Home bookmarked locations chip row."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors


def build_bookmarks_section(
    bookmarks: list[dict],
    on_select_bookmark: Callable,
) -> ft.Container | None:
    """Builds the horizontal scrollable chips for saved bookmarked locations."""
    if not bookmarks:
        return None

    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(
                    ft.Icons.BOOKMARK_ROUNDED,
                    size=tokens.ICON_XS,
                    color=AppColors.WARNING,
                ),
                *(
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text(
                                        b.get("name", "Saved"),
                                        size=tokens.FONT_XS,
                                        weight=ft.FontWeight.W_600,
                                        color=ft.Colors.ON_SURFACE,
                                    ),
                                ],
                                spacing=2,
                                tight=True,
                            ),
                            padding=ft.Padding(tokens.SPACE_SM, 4, tokens.SPACE_SM, 4),
                            border_radius=tokens.RADIUS_FULL,
                            bgcolor=ft.Colors.with_opacity(0.12, AppColors.WARNING),
                            border=ft.Border.all(
                                1,
                                ft.Colors.with_opacity(0.25, AppColors.WARNING),
                            ),
                            on_click=lambda _, loc=b: (
                                asyncio.create_task(
                                    on_select_bookmark(
                                        loc["latitude"],
                                        loc["longitude"],
                                        loc["name"],
                                        loc.get("country", ""),
                                    )
                                )
                                if on_select_bookmark
                                else None
                            ),
                        )
                        for b in bookmarks
                    ]
                ),
            ],
            spacing=tokens.SPACE_XS,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=ft.Padding(tokens.SPACE_LG, tokens.SPACE_XS, tokens.SPACE_LG, 0),
    )
