"""MapScreen — Full-Screen Planetary Hazard Radar with real-time filters and tap-to-inspect."""

from __future__ import annotations

import asyncio
import logging

import flet as ft
from flet import Control

from components.hazard_map import HazardMap, build_event_detail_sheet
from components.map.map_scan_section import build_map_scan_section
from core import tokens
from core.theme import AppColors, is_dark_mode
from hooks.use_map_center import use_map_center
from services.ai_service import DEFAULT_SCAN_QUESTION, stream_map_scan
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.map")


@ft.component
def MapScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    active_filter, set_active_filter = ft.use_state("all")
    selected_event, set_selected_event = ft.use_state(None)
    satellite, set_satellite = ft.use_state(False)
    map_ref = ft.use_ref(None)
    scan_ref = ft.use_ref(None)  # ft.Screenshot wrapping the map — the capture source

    # AI map-scan state — captures the live map view, streams a visual read
    scan_open, set_scan_open = ft.use_state(False)
    scan_answer, set_scan_answer = ft.use_state("")
    scan_busy, set_scan_busy = ft.use_state(False)
    scan_unavailable, set_scan_unavailable = ft.use_state(False)
    scan_question, set_scan_question = ft.use_state("")
    scan_model, set_scan_model = ft.use_state("")

    async def _run_scan(q: str):
        if scan_busy:
            return
        shot = scan_ref.current
        if shot is None:
            logger.warning("Map capture skipped: screenshot control missing")
            return
        set_scan_busy(True)
        set_scan_answer("")
        set_scan_unavailable(False)
        set_scan_model("")
        try:
            # pixel_ratio 1 keeps the capture far under the gateway's 10MB cap
            png = await shot.capture(pixel_ratio=1.0)
        except Exception as ex:
            logger.warning("Map capture failed: %s", ex)
            set_scan_unavailable(True)
            set_scan_busy(False)
            return

        chunks: list[str] = []

        def _collect(chunk: str):
            chunks.append(chunk)
            set_scan_answer("".join(chunks))

        try:
            result = await stream_map_scan(png, q, _collect)
            set_scan_answer(result.text or "".join(chunks))
            set_scan_model(result.model)
            if not (result.text or chunks):
                set_scan_unavailable(True)
        except Exception as ex:
            logger.warning("AI map scan failed: %s", ex)
            set_scan_unavailable(True)
        finally:
            set_scan_busy(False)

    def _on_scan(e=None, close_only: bool = False):
        if close_only:
            set_scan_open(False)
            set_scan_answer("")
            return
        set_scan_open(True)
        asyncio.create_task(_run_scan(DEFAULT_SCAN_QUESTION))

    def _on_scan_ask(e=None):
        q = scan_question
        set_scan_question("")
        asyncio.create_task(_run_scan(q))

    # Follow the active focus point (search / GPS / suggestion selections)
    use_map_center(map_ref, state.current_lat, state.current_lon, 10.0)

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

    from flet import context as flet_context

    page = flet_context.page
    is_dark = is_dark_mode(page)

    # Filter Chips
    sat_chip = ft.Container(
        content=ft.Row(
            [
                ft.Icon(
                    ft.Icons.SATELLITE_ROUNDED,
                    size=14,
                    color=AppColors.PRIMARY
                    if satellite
                    else ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Text(
                    "Satellite",
                    size=tokens.FONT_XS,
                    weight=ft.FontWeight.W_600,
                    color=AppColors.PRIMARY if satellite else ft.Colors.ON_SURFACE,
                ),
            ],
            spacing=4,
            tight=True,
        ),
        padding=ft.Padding(10, 6, 10, 6),
        border_radius=tokens.RADIUS_FULL,
        bgcolor=ft.Colors.with_opacity(0.18, AppColors.PRIMARY)
        if satellite
        else (
            ft.Colors.with_opacity(0.85, AppColors.DARK_SURFACE)
            if is_dark
            else ft.Colors.WHITE
        ),
        border=ft.Border.all(
            1, AppColors.PRIMARY if satellite else AppColors.get_border(page)
        ),
        on_click=lambda _: set_satellite(not satellite),
        ink=True,
    )

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
        sat_chip,
        *[
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
                                color
                                if active_filter == f_key
                                else ft.Colors.ON_SURFACE
                            ),
                        ),
                    ],
                    spacing=4,
                    tight=True,
                ),
                padding=ft.Padding(10, 6, 10, 6),
                border_radius=tokens.RADIUS_FULL,
                bgcolor=(
                    ft.Colors.with_opacity(0.18, color)
                    if active_filter == f_key
                    else (
                        ft.Colors.with_opacity(0.85, AppColors.DARK_SURFACE)
                        if is_dark
                        else ft.Colors.with_opacity(0.92, AppColors.LIGHT_SURFACE)
                    )
                ),
                border=ft.Border.all(
                    1,
                    (
                        color
                        if active_filter == f_key
                        else (
                            ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
                            if is_dark
                            else ft.Colors.with_opacity(0.15, ft.Colors.BLACK)
                        )
                    ),
                ),
                on_click=lambda _, key=f_key: set_active_filter(key),
            )
            for f_key, label, icon, color in chips
        ],
    ]

    return ft.Stack(
        controls=[
            # Full Map Layer with CircleLayer shockwaves & map tap — wrapped in
            # Screenshot so the AI scan can capture the exact visible view.
            ft.Screenshot(
                content=HazardMap(
                    lat=state.current_lat,
                    lon=state.current_lon,
                    zoom=3.0,
                    earthquakes=filtered_earthquakes,
                    disasters=filtered_disasters,
                    on_marker_click=_on_marker_click,
                    on_map_tap=_on_map_tap,
                    expand=True,
                    is_dark=is_dark,
                    satellite=satellite,
                    map_ref=map_ref,
                ),
                expand=True,
                ref=scan_ref,
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
            # Floating AI Scan pill (bottom-right)
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.AUTO_AWESOME_ROUNDED,
                            size=tokens.ICON_XS,
                            color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            "AI Scan",
                            size=tokens.FONT_XS,
                            weight=ft.FontWeight.W_600,
                            color=ft.Colors.WHITE,
                        ),
                    ],
                    spacing=tokens.SPACE_XXS,
                    tight=True,
                ),
                padding=ft.Padding(
                    tokens.SPACE_MD, tokens.SPACE_XS, tokens.SPACE_MD, tokens.SPACE_XS
                ),
                border_radius=tokens.RADIUS_FULL,
                bgcolor=AppColors.ATMOSPHERE,
                shadow=ft.BoxShadow(
                    spread_radius=1, blur_radius=8, color=AppColors.ATMOSPHERE
                ),
                on_click=lambda _: _on_scan(),
                ink=True,
                right=tokens.SPACE_LG,
                bottom=tokens.SPACE_LG,
            ),
            # AI Scan answer panel (bottom overlay, above the pill)
            *(
                [
                    ft.Container(
                        content=build_map_scan_section(
                            scan_answer,
                            scan_busy,
                            scan_unavailable,
                            scan_question,
                            scan_model,
                            _on_scan,
                            _on_scan_ask,
                            lambda e: set_scan_question(e.control.value or ""),
                        ),
                        left=tokens.SPACE_LG,
                        right=tokens.SPACE_LG,
                        bottom=tokens.SPACE_LG,
                    )
                ]
                if scan_open
                else []
            ),
            # Selected Marker Telemetry Sheet (Bottom overlay)
            *(
                [
                    build_event_detail_sheet(
                        selected_event,
                        on_close=_close_event_sheet,
                        on_open_url=lambda u: (
                            asyncio.create_task(controller.launch_url(u))
                            if controller.launch_url
                            else None
                        ),
                    )
                ]
                if selected_event
                else []
            ),
        ],
        expand=True,
    )
