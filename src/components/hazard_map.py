"""Interactive Multi-Layer Planetary Hazard Map with flet-map."""

from __future__ import annotations

import logging
from collections.abc import Callable

import flet as ft
import flet_map as map

from core import tokens
from core.theme import AppColors

logger = logging.getLogger("asase.map")


def build_hazard_marker(
    item: dict,
    on_click: Callable[[dict], None] | None = None,
) -> map.Marker:
    """Creates a custom pulsing marker for earthquakes, wildfires, and floods."""
    m_type = item.get("type", "earthquake")
    lat = float(item.get("latitude", 0.0))
    lon = float(item.get("longitude", 0.0))

    if m_type == "earthquake":
        mag = float(item.get("magnitude", 2.5))
        size = max(18.0, min(36.0, mag * 5.0))
        color = (
            AppColors.SEVERITY_CRITICAL
            if mag >= 6.5
            else (
                AppColors.SEVERITY_HIGH if mag >= 4.5 else AppColors.SEVERITY_MODERATE
            )
        )
        icon_data = ft.Icons.WAVES_ROUNDED
    elif m_type == "wildfire":
        size = 24.0
        color = AppColors.SEVERITY_CRITICAL
        icon_data = ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED
    elif m_type == "flood":
        size = 24.0
        color = AppColors.OCEAN
        icon_data = ft.Icons.WATER_DAMAGE_ROUNDED
    else:
        size = 22.0
        color = AppColors.WARNING
        icon_data = ft.Icons.WARNING_AMBER_ROUNDED

    marker_content = ft.Container(
        content=ft.Icon(icon_data, size=size * 0.7, color=ft.Colors.WHITE),
        width=size,
        height=size,
        border_radius=size / 2.0,
        bgcolor=color,
        border=ft.Border.all(2, ft.Colors.WHITE),
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=6,
            color=ft.Colors.with_opacity(0.5, color),
        ),
        alignment=ft.Alignment.CENTER,
        tooltip=f"{item.get('title', 'Hazard')}",
        on_click=lambda _: on_click(item) if on_click else None,
    )

    return map.Marker(
        content=marker_content,
        coordinates=map.MapLatitudeLongitude(lat, lon),
        width=size,
        height=size,
        rotate=True,
    )


def build_seismic_shockwave_circles(earthquakes: list[dict]) -> list[map.CircleMarker]:
    """Builds true geodesic meter-radius shockwave circles around earthquakes."""
    circles: list[map.CircleMarker] = []
    for eq in earthquakes[:40]:
        mag = float(eq.get("magnitude", 2.5))
        lat = float(eq.get("latitude", 0.0))
        lon = float(eq.get("longitude", 0.0))

        # Seismic felt radius in meters: e.g. M5.0 ~ 50km, M7.0 ~ 200km
        radius_m = (10 ** (0.5 * mag)) * 1500.0
        radius_m = max(15000.0, min(350000.0, radius_m))

        color = (
            AppColors.SEVERITY_CRITICAL
            if mag >= 6.5
            else (
                AppColors.SEVERITY_HIGH if mag >= 4.5 else AppColors.SEVERITY_MODERATE
            )
        )

        circles.append(
            map.CircleMarker(
                coordinates=map.MapLatitudeLongitude(lat, lon),
                radius=radius_m,
                use_radius_in_meter=True,
                color=ft.Colors.with_opacity(0.08, color),
                border_color=ft.Colors.with_opacity(0.35, color),
                border_stroke_width=1.5,
            )
        )
    return circles


def HazardMap(
    lat: float = 6.5244,
    lon: float = 3.3792,
    zoom: float = 3.0,
    earthquakes: list[dict] | None = None,
    disasters: list[dict] | None = None,
    on_marker_click: Callable[[dict], None] | None = None,
    on_map_tap: Callable[[float, float], None] | None = None,
    expand: bool = True,
    height: float | None = None,
) -> ft.Control:
    """Builds the interactive multi-layer planetary map with CircleLayer shockwaves."""
    markers: list[map.Marker] = []
    circle_markers: list[map.CircleMarker] = []

    if earthquakes:
        circle_markers.extend(build_seismic_shockwave_circles(earthquakes))
        for eq in earthquakes[:80]:
            markers.append(build_hazard_marker(eq, on_click=on_marker_click))

    if disasters:
        for dis in disasters[:50]:
            markers.append(build_hazard_marker(dis, on_click=on_marker_click))

    # User Focus Marker
    user_marker = map.Marker(
        content=ft.Container(
            content=ft.Icon(
                ft.Icons.LOCATION_ON_ROUNDED, size=26, color=AppColors.PRIMARY
            ),
            shadow=ft.BoxShadow(
                spread_radius=1, blur_radius=8, color=AppColors.PRIMARY
            ),
        ),
        coordinates=map.MapLatitudeLongitude(lat, lon),
        width=32,
        height=32,
        rotate=True,
    )
    markers.append(user_marker)

    # CartoDB Dark Matter tile template with OpenStreetMap fallback
    tile_layer = map.TileLayer(
        url_template="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
        fallback_url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        subdomains=["a", "b", "c", "d"],
        user_agent_package_name="ng.kiri.asase",
        keep_buffer=2,
        pan_buffer=1,
    )

    circle_layer = map.CircleLayer(circles=circle_markers)
    marker_layer = map.MarkerLayer(markers=markers)

    def _on_tap_handler(e: map.MapTapEvent):
        if on_map_tap and e.coordinates:
            on_map_tap(e.coordinates.latitude, e.coordinates.longitude)

    return ft.Container(
        content=map.Map(
            layers=[tile_layer, circle_layer, marker_layer],
            initial_center=map.MapLatitudeLongitude(lat, lon),
            initial_zoom=zoom,
            bgcolor="#0B0F17",
            keep_alive=True,
            on_tap=_on_tap_handler,
            expand=expand,
        ),
        border_radius=tokens.RADIUS_LG,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.12, ft.Colors.WHITE)),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        expand=expand,
        height=height,
    )
