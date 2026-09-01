"""HistoryScreen — chronological recent searches & bookmarks with clear-all."""

from __future__ import annotations

import asyncio

import flet as ft
from flet import Control

from components.app_header import build_app_header
from components.empty_state import EmptyState
from components.section_header import SectionHeader
from core import tokens
from core.theme import AppColors, AppStyles
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx


@ft.component
def HistoryScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)
    _ = (state.telemetry_version, len(state.recent_searches), len(state.bookmarks))

    from flet import context as flet_context

    page = flet_context.page

    def _clear(e=None):
        async def _do():
            if controller.save_setting:
                from core.constants import STORAGE_RECENT_SEARCHES

                state.recent_searches = []
                await controller.save_setting(STORAGE_RECENT_SEARCHES, [])
                try:
                    if page:
                        page.update()
                except Exception:
                    pass

        asyncio.create_task(_do())

    header = build_app_header(
        page,
        title="History",
        subtitle="SAVED LOCATIONS & RECENT SEARCHES",
        on_refresh=controller.refresh_all,
    )

    # Clear-all action preserved from the old inline header, shown only when
    # there is something to clear.
    clear_row = (
        ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        f"{len(state.recent_searches)} locations • {len(state.bookmarks)} bookmarks",
                        size=tokens.FONT_XS,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        expand=True,
                    ),
                    ft.TextButton("Clear All", on_click=_clear)
                    if state.recent_searches
                    else ft.Container(),
                ],
                spacing=tokens.SPACE_MD,
            ),
            padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_XS),
        )
        if (state.recent_searches or state.bookmarks)
        else ft.Container()
    )

    def _row(item: dict, is_bookmark: bool = False):
        loc_name = item.get("name", "—")
        country = item.get("country", "")
        lat = float(item.get("lat", item.get("latitude", 0)))
        lon = float(item.get("lon", item.get("longitude", 0)))

        def _tap(e=None):
            if controller.select_coordinates:
                asyncio.create_task(
                    controller.select_coordinates(lat, lon, loc_name, country)
                )

        return AppStyles.glass_card(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.BOOKMARK_ROUNDED
                            if is_bookmark
                            else ft.Icons.HISTORY_ROUNDED,
                            size=tokens.ICON_SM,
                            color=AppColors.PRIMARY,
                        ),
                        width=36,
                        height=36,
                        border_radius=18,
                        bgcolor=ft.Colors.with_opacity(0.12, AppColors.PRIMARY),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                loc_name,
                                size=tokens.FONT_SM,
                                weight=ft.FontWeight.W_600,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                f"{country} • {lat:.2f}, {lon:.2f}",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                max_lines=1,
                            ),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ARROW_OUTWARD_ROUNDED,
                        icon_size=18,
                        tooltip="Go",
                        on_click=_tap,
                    ),
                ],
                spacing=tokens.SPACE_MD,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=tokens.SPACE_MD,
            on_click=_tap,
        )

    if not state.recent_searches and not state.bookmarks:
        body = EmptyState(
            icon=ft.Icons.HISTORY_ROUNDED,
            title="No history yet",
            subtitle="Search a city or tap the map to start exploring.",
            action_text="Explore Map",
            on_action=lambda: controller.show_map() if controller.show_map else None,
        )
    else:
        rows = []
        if state.bookmarks:
            rows.append(SectionHeader("BOOKMARKS"))
            for b in state.bookmarks:
                rows.append(
                    ft.Container(
                        content=_row(b, True),
                        padding=ft.Padding(
                            tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_XS
                        ),
                    )
                )
        if state.recent_searches:
            rows.append(SectionHeader("RECENT SEARCHES"))
            for r in state.recent_searches[:20]:
                rows.append(
                    ft.Container(
                        content=_row(r, False),
                        padding=ft.Padding(
                            tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_XS
                        ),
                    )
                )
        body = ft.Column(rows, spacing=tokens.SPACE_XS)

    return ft.ListView(
        controls=[
            header,
            clear_row,
            ft.Container(content=body, padding=ft.Padding(0, tokens.SPACE_SM, 0, 0)),
            ft.Container(height=tokens.SPACE_XXXL),
        ],
        expand=True,
        spacing=0,
    )
