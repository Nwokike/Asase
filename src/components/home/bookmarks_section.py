"""Home bookmarked locations chip row."""

from __future__ import annotations

import logging
from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors

logger = logging.getLogger("asase.bookmarks")


def _safe_coords(bookmark: dict) -> tuple[float, float] | None:
    """Parse bookmark coordinates; None when corrupt (never raise in UI)."""
    try:
        return (
            float(bookmark.get("latitude", bookmark.get("lat"))),
            float(bookmark.get("longitude", bookmark.get("lon"))),
        )
    except (TypeError, ValueError):
        logger.debug("Skipping bookmark with corrupt coordinates: %r", bookmark)
        return None


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
                            # NOTE: on_select_bookmark is the (sync) screen
                            # wrapper that schedules the async controller
                            # call itself — do NOT wrap it in create_task
                            # (create_task(None) raises TypeError).
                            on_click=lambda _, loc=b: (
                                on_select_bookmark(
                                    *_safe_coords(loc),
                                    loc.get("name", "Saved"),
                                    loc.get("country", ""),
                                )
                                if on_select_bookmark and _safe_coords(loc)
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
