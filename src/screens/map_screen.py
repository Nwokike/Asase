"""MapScreen — Full-Screen Planetary Hazard Radar with real-time filters and tap-to-inspect."""

from __future__ import annotations

import logging

import flet as ft
from flet import Control

from components.hazard_map import HazardMap, build_event_detail_sheet
from components.map.map_scan_section import build_map_scan_section
from core import tokens
from core.tasks import schedule
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

    # Multi-select layer model: each hazard type toggles independently.
    # "all" is a convenience toggle, not a filter mode.
    active_layers, set_active_layers = ft.use_state({"earthquake", "wildfire", "storm"})
    selected_event, set_selected_event = ft.use_state(None)
    satellite, set_satellite = ft.use_state(False)
    map_ref = ft.use_ref(None)
    scan_ref = ft.use_ref(None)  # ft.Screenshot wrapping the map — the capture source

    from flet import context as flet_context

    page = flet_context.page

    # AI map-scan state — captures the live map view, streams a visual read
    scan_open, set_scan_open = ft.use_state(False)
    scan_answer, set_scan_answer = ft.use_state("")
    scan_busy, set_scan_busy = ft.use_state(False)
    scan_unavailable, set_scan_unavailable = ft.use_state(False)
    scan_question, set_scan_question = ft.use_state("")
    scan_model, set_scan_model = ft.use_state("")
    # Ref-based guard: two rapid taps both read the render-time scan_busy
    # as False and fire duplicate captures — the ref is immediate.
    scan_busy_guard = ft.use_ref(False)

    async def _run_scan(q: str):
        if scan_busy_guard.current:
            return
        shot = scan_ref.current
        if shot is None:
            logger.warning("Map capture skipped: screenshot control missing")
            return
        scan_busy_guard.current = True
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
            scan_busy_guard.current = False
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
            scan_busy_guard.current = False
            set_scan_busy(False)

    def _on_scan(e=None, close_only: bool = False):
        if close_only:
            set_scan_open(False)
            set_scan_answer("")
            return
        set_scan_open(True)
        schedule(_run_scan, DEFAULT_SCAN_QUESTION, page=page)

    def _on_scan_ask(e=None):
        q = scan_question
        set_scan_question("")
        schedule(_run_scan, q, page=page)

    # Follow the active focus point (search / GPS / suggestion selections)
    use_map_center(map_ref, state.current_lat, state.current_lon, 10.0)

    # Filter events based on active layers (multi-select)
    filtered_earthquakes = state.earthquakes if "earthquake" in active_layers else []
    filtered_disasters = [d for d in state.disasters if d.get("type") in active_layers]

    def _on_marker_click(event: dict):
        set_selected_event(event)

    def _close_event_sheet(e=None):
        set_selected_event(None)

    def _on_map_tap(lat: float, lon: float):
        if controller.select_coordinates:
            schedule(
                controller.select_coordinates,
                lat,
                lon,
                f"Coord ({lat:.2f}, {lon:.2f})",
                "",
                page=page,
            )

    def _open_event_dossier():
        """Re-center tracking to the selected marker and open the Dossier."""
        ev = selected_event or {}
        lat = float(ev.get("latitude", 0.0))
        lon = float(ev.get("longitude", 0.0))
        name = ev.get("place") or ev.get("title") or f"Coord ({lat:.2f}, {lon:.2f})"

        async def _go():
            set_selected_event(None)
            if controller.select_coordinates:
                await controller.select_coordinates(lat, lon, name, "")
            if controller.open_report:
                await controller.open_report()

        schedule(_go, page=page)

    def _share_event_text(msg: str):
        if controller.share_text:
            schedule(controller.share_text, msg, "Asase Hazard Alert", page=page)

    is_dark = is_dark_mode(page)

    # Right-edge vertical layer stack (Windy-style): each hazard type
    # toggles independently; satellite is a basemap switch.
    def _toggle_layer(layer: str):
        if layer == "all":
            # Toggle all on/off
            if active_layers == {"earthquake", "wildfire", "storm"}:
                set_active_layers(set())
            else:
                set_active_layers({"earthquake", "wildfire", "storm"})
        else:
            new_layers = set(active_layers)
            if layer in new_layers:
                new_layers.discard(layer)
            else:
                new_layers.add(layer)
            set_active_layers(new_layers)

    layer_buttons = [
        ("satellite", ft.Icons.SATELLITE_ROUNDED, "Satellite basemap", satellite),
        (
            "earthquake",
            ft.Icons.WAVES_ROUNDED,
            "Seismic",
            "earthquake" in active_layers,
        ),
        (
            "wildfire",
            ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
            "Wildfires",
            "wildfire" in active_layers,
        ),
        ("storm", ft.Icons.CYCLONE_ROUNDED, "Storms", "storm" in active_layers),
    ]

    layer_stack = ft.Container(
        content=ft.Column(
            [
                ft.IconButton(
                    icon=icon,
                    icon_size=20,
                    icon_color=AppColors.PRIMARY
                    if active
                    else ft.Colors.ON_SURFACE_VARIANT,
                    tooltip=tooltip,
                    on_click=lambda _, key=key: (
                        set_satellite(not satellite)
                        if key == "satellite"
                        else _toggle_layer(key)
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.with_opacity(0.15, AppColors.PRIMARY)
                        if active
                        else ft.Colors.with_opacity(0.85, AppColors.DARK_SURFACE)
                        if is_dark
                        else ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD),
                        padding=8,
                    ),
                )
                for key, icon, tooltip, active in layer_buttons
            ],
            spacing=tokens.SPACE_SM,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=48,
        top=tokens.SPACE_SM,
        right=tokens.SPACE_SM,
    )

    # Threat mini-strip: critical/high counts, tappable to dossier
    from core.units import feed_age

    critical_count = sum(
        1 for e in state.earthquakes if e.get("severity") == "critical"
    ) + sum(1 for d in state.disasters if d.get("type") == "wildfire")
    high_count = sum(1 for e in state.earthquakes if e.get("severity") == "high") + sum(
        1 for d in state.disasters if d.get("type") == "storm"
    )
    usgs_age = feed_age("usgs")

    threat_strip = None
    if critical_count or high_count:
        parts = []
        if critical_count:
            parts.append(f"{critical_count} critical")
        if high_count:
            parts.append(f"{high_count} elevated")
        threat_strip = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.WARNING_AMBER_ROUNDED,
                        size=tokens.ICON_XS,
                        color=AppColors.SEVERITY_CRITICAL
                        if critical_count
                        else AppColors.SEVERITY_HIGH,
                    ),
                    ft.Text(
                        " ".join(parts) + " nearby",
                        size=tokens.FONT_XS,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.Container(expand=True),
                    ft.Text(
                        f"USGS {usgs_age}",
                        style=AppColors.data_text_style(size=tokens.FONT_XXS),
                    ),
                ],
                spacing=tokens.SPACE_XS,
                tight=True,
            ),
            padding=ft.Padding(
                tokens.SPACE_MD, tokens.SPACE_XS, tokens.SPACE_MD, tokens.SPACE_XS
            ),
            border_radius=tokens.RADIUS_FULL,
            bgcolor=ft.Colors.with_opacity(
                0.12,
                AppColors.SEVERITY_CRITICAL
                if critical_count
                else AppColors.SEVERITY_HIGH,
            ),
            border=ft.Border.all(
                1,
                ft.Colors.with_opacity(
                    0.25,
                    AppColors.SEVERITY_CRITICAL
                    if critical_count
                    else AppColors.SEVERITY_HIGH,
                ),
            ),
            bottom=tokens.SPACE_SM,
            left=tokens.SPACE_LG,
            right=tokens.SPACE_LG,
            on_click=lambda _: (
                schedule(controller.open_report, page=page)
                if controller.open_report
                else None
            ),
            ink=True,
        )

    # Empty-filter state
    empty_filter = None
    if not filtered_earthquakes and not filtered_disasters and not state.is_loading:
        empty_filter = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(
                        ft.Icons.FILTER_ALT_OFF_ROUNDED,
                        size=36,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Text(
                        "No events match this filter",
                        size=tokens.FONT_SM,
                        weight=ft.FontWeight.W_600,
                        color=ft.Colors.ON_SURFACE,
                    ),
                    ft.Text(
                        "Try enabling more layers or clearing the filter.",
                        size=tokens.FONT_XS,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                spacing=tokens.SPACE_XS,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            alignment=ft.Alignment.CENTER,
            expand=True,
        )

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
            # Right-edge vertical layer stack (Windy-style)
            layer_stack,
            # Threat mini-strip (bottom, above AI pill)
            *([threat_strip] if threat_strip else []),
            # Empty-filter state
            *([empty_filter] if empty_filter else []),
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
                # Sit above the threat strip when it's showing (full-width)
                bottom=tokens.SPACE_SM + 44 if threat_strip else tokens.SPACE_LG,
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
                            is_dark=is_dark,
                            on_open_link=(
                                lambda url: (
                                    schedule(controller.launch_url, url, page=page)
                                    if controller.launch_url
                                    else None
                                )
                            ),
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
                            schedule(controller.launch_url, u, page=page)
                            if controller.launch_url
                            else None
                        ),
                        on_view_dossier=_open_event_dossier,
                        on_share=_share_event_text,
                    )
                ]
                if selected_event
                else []
            ),
        ],
        expand=True,
    )
