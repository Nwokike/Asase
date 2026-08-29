"""MapScreen — Full-Screen Planetary Hazard Radar with real-time filters and tap-to-inspect."""

from __future__ import annotations

import asyncio

import flet as ft
from flet import Control

from components.hazard_map import HazardMap
from core import tokens
from core.theme import AppColors
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx


@ft.component
def MapScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    active_filter, set_active_filter = ft.use_state("all")
    selected_event, set_selected_event = ft.use_state(None)

    # Filter events based on active chip
    filtered_earthquakes = (
        state.earthquakes if active_filter in ("all", "earthquake") else []
    )
    filtered_disasters = (
        [
            d
            for d in state.disasters
            if (active_filter == "all")
            or (active_filter == "fire" and d.get("type") == "wildfire")
            or (active_filter == "storm" and d.get("type") == "storm")
        ]
        if active_filter in ("all", "fire", "storm")
        else []
    )

    def _on_marker_click(event: dict):
        set_selected_event(event)

    def _close_event_sheet(e=None):
        set_selected_event(None)

    def _on_map_tap(lat: float, lon: float):
        if controller.select_coordinates:
            asyncio.create_task(
                controller.select_coordinates(
                    lat, lon, f"Coord ({lat:.2f}, {lon:.2f})", ""
                )
            )

    # Filter Chips
    chips = [
        ("all", "All Hazards", ft.Icons.PUBLIC_ROUNDED, AppColors.PRIMARY),
        (
            "earthquake",
            f"Seismic ({len(state.earthquakes)})",
            ft.Icons.WAVES_ROUNDED,
            AppColors.SEVERITY_HIGH,
        ),
        (
            "fire",
            "Wildfires",
            ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
            AppColors.SEVERITY_CRITICAL,
        ),
        ("storm", "Storms", ft.Icons.CYCLONE_ROUNDED, AppColors.OCEAN),
    ]

    chip_controls = [
        ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        icon,
                        size=14,
                        color=(
                            color
                            if active_filter == f_key
                            else ft.Colors.ON_SURFACE_VARIANT
                        ),
                    ),
                    ft.Text(
                        label,
                        size=tokens.FONT_XS,
                        weight=(
                            ft.FontWeight.W_700
                            if active_filter == f_key
                            else ft.FontWeight.W_500
                        ),
                        color=(
                            color if active_filter == f_key else ft.Colors.ON_SURFACE
                        ),
                    ),
                ],
                spacing=4,
                tight=True,
            ),
            padding=ft.Padding(10, 6, 10, 6),
            border_radius=tokens.RADIUS_FULL,
            bgcolor=(
                ft.Colors.with_opacity(0.15, color)
                if active_filter == f_key
                else ft.Colors.with_opacity(0.6, AppColors.DARK_SURFACE)
            ),
            border=ft.Border.all(
                1,
                (
                    color
                    if active_filter == f_key
                    else ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
                ),
            ),
            on_click=lambda _, key=f_key: set_active_filter(key),
        )
        for f_key, label, icon, color in chips
    ]

    return ft.Stack(
        controls=[
            # Full Map Layer with CircleLayer shockwaves & map tap
            HazardMap(
                lat=state.current_lat,
                lon=state.current_lon,
                zoom=3.0,
                earthquakes=filtered_earthquakes,
                disasters=filtered_disasters,
                on_marker_click=_on_marker_click,
                on_map_tap=_on_map_tap,
                expand=True,
            ),
            # Floating Top Filter Bar
            ft.Container(
                content=ft.Row(
                    chip_controls,
                    scroll=ft.ScrollMode.AUTO,
                    spacing=tokens.SPACE_SM,
                ),
                top=tokens.SPACE_SM,
                left=tokens.SPACE_LG,
                right=tokens.SPACE_LG,
            ),
            # Selected Marker Telemetry Sheet (Bottom overlay)
            *(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.Icons.WARNING_ROUNDED,
                                                    color=AppColors.PRIMARY,
                                                    size=tokens.ICON_SM,
                                                ),
                                                ft.Text(
                                                    selected_event.get(
                                                        "type", "Event"
                                                    ).upper(),
                                                    size=tokens.FONT_XS,
                                                    weight=ft.FontWeight.W_700,
                                                    color=AppColors.PRIMARY,
                                                ),
                                            ],
                                            spacing=4,
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.CLOSE_ROUNDED,
                                            icon_size=18,
                                            on_click=_close_event_sheet,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Text(
                                    selected_event.get("title", "Hazard Detail"),
                                    size=tokens.FONT_MD,
                                    weight=ft.FontWeight.BOLD,
                                    font_family="Outfit",
                                ),
                                ft.Text(
                                    f"Coordinates: {selected_event.get('latitude', 0.0):.4f}°, {selected_event.get('longitude', 0.0):.4f}° • Depth: {selected_event.get('depth_km', 0.0)} km",
                                    size=tokens.FONT_XS,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                            spacing=tokens.SPACE_XXS,
                            tight=True,
                        ),
                        bottom=tokens.SPACE_LG,
                        left=tokens.SPACE_LG,
                        right=tokens.SPACE_LG,
                        padding=tokens.SPACE_MD,
                        border_radius=tokens.RADIUS_LG,
                        bgcolor=AppColors.DARK_SURFACE,
                        border=ft.Border.all(
                            1,
                            ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                        ),
                        shadow=ft.BoxShadow(
                            spread_radius=2,
                            blur_radius=12,
                            color=ft.Colors.BLACK,
                        ),
                    )
                ]
                if selected_event
                else []
            ),
        ],
        expand=True,
    )
