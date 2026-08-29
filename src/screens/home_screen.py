"""HomeScreen — Real-Time Multi-Hazard Planetary Radar, Active Feeds & Bookmarks."""

from __future__ import annotations

import asyncio
import logging

import flet as ft
from flet import Control

from components.app_header import build_app_header
from components.banner_ad import AdMobBanner
from components.hazard_map import HazardMap
from components.home.active_alert_banner import build_active_alert_banner
from components.home.bookmarks_section import build_bookmarks_section
from components.home.location_search_bar import build_location_search_bar
from components.home.summary_cards_row import build_quick_metrics_row
from components.section_header import SectionHeader
from components.skeleton_loader import TelemetrySkeletonCard
from components.telemetry_card import TelemetryCard
from core import tokens
from core.geo_utils import calculate_haversine_distance_km
from services.geocoding_service import GeocodingService
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.home")


@ft.component
def HomeScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    search_query, set_search_query = ft.use_state("")
    search_results, set_search_results = ft.use_state([])
    _is_searching, set_is_searching = ft.use_state(False)

    async def _on_search_change(e):
        q = e.control.value
        set_search_query(q)
        if len(q.strip()) >= 2:
            set_is_searching(True)
            results = await GeocodingService.search_cities(q)
            set_search_results(results)
            set_is_searching(False)
        else:
            set_search_results([])

    def _select_city(city: dict):
        if controller.select_coordinates:
            asyncio.create_task(
                controller.select_coordinates(
                    city["latitude"],
                    city["longitude"],
                    city["name"],
                    city.get("country", ""),
                )
            )
            set_search_query("")
            set_search_results([])

    # Find closest active hazard to user
    closest_hazard = None
    min_dist_km = 999999.0
    for eq in state.earthquakes:
        lat = float(eq.get("latitude", 0.0))
        lon = float(eq.get("longitude", 0.0))
        d = calculate_haversine_distance_km(
            state.current_lat, state.current_lon, lat, lon
        )
        if d < min_dist_km:
            min_dist_km = d
            closest_hazard = (eq, d, "earthquake")

    for dis in state.disasters:
        lat = float(dis.get("latitude", 0.0))
        lon = float(dis.get("longitude", 0.0))
        d = calculate_haversine_distance_km(
            state.current_lat, state.current_lon, lat, lon
        )
        if d < min_dist_km:
            min_dist_km = d
            closest_hazard = (dis, d, dis.get("type", "hazard"))

    # Air Quality Summary
    aqi_current = state.air_quality_data.get("current", {})
    us_aqi = aqi_current.get("us_aqi", "--")
    pm25 = aqi_current.get("pm2_5", "--")

    # Space Weather Summary
    kp_val = state.space_weather.get("kp_index", "--")
    space_status = state.space_weather.get("geomagnetic_status", "Normal")

    from flet import context as flet_context

    page = flet_context.page

    header_view = build_app_header(
        page,
        title="Asase",
        subtitle="EARTH INTELLIGENCE",
        on_refresh=controller.refresh_all,
        on_settings=lambda: (
            controller.navigate_tab(3) if controller.navigate_tab else None
        ),
        save_setting_fn=controller.save_setting,
    )

    search_bar = build_location_search_bar(
        page,
        search_query,
        search_results,
        _on_search_change,
        _select_city,
        controller.locate_user,
    )
    bookmarks_bar = build_bookmarks_section(
        state.bookmarks, controller.select_coordinates
    )
    alert_banner = build_active_alert_banner(
        closest_hazard,
        lambda: controller.show_map() if controller.show_map else None,
    )
    metrics_row = build_quick_metrics_row(
        len(state.earthquakes),
        state.min_magnitude_filter,
        us_aqi,
        pm25,
        kp_val,
        space_status,
    )

    return ft.ListView(
        controls=[
            header_view,
            search_bar,
            *([bookmarks_bar] if bookmarks_bar else []),
            *([alert_banner] if alert_banner else []),
            metrics_row,
            # Embedded Planetary Map Widget
            SectionHeader(
                "GLOBAL HAZARD RADAR",
                action_text="EXPAND MAP",
                on_action=lambda _: (
                    controller.show_map() if controller.show_map else None
                ),
            ),
            ft.Container(
                content=HazardMap(
                    lat=state.current_lat,
                    lon=state.current_lon,
                    zoom=2.5,
                    earthquakes=state.earthquakes,
                    disasters=state.disasters,
                    expand=False,
                    height=240,
                ),
                padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
            ),
            # Real-Time Seismic Stream
            SectionHeader("RECENT SEISMIC ACTIVITY (USGS 24H)"),
            *(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                TelemetrySkeletonCard(height=95),
                                TelemetrySkeletonCard(height=95),
                            ],
                            spacing=tokens.SPACE_SM,
                        ),
                        padding=ft.Padding(
                            tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                        ),
                    )
                ]
                if state.is_loading and not state.earthquakes
                else [
                    ft.Container(
                        content=ft.Column(
                            [
                                TelemetryCard(
                                    title=eq.get("place", "Earthquake"),
                                    subtitle=f"Magnitude M{eq.get('magnitude', 0):.1f} • Depth {eq.get('depth_km', 0):.1f}km • {eq.get('time_str', '')}",
                                    value=f"MMI {eq.get('mmi', 0.0):.1f}"
                                    if eq.get("mmi")
                                    else "",
                                    severity=eq.get("severity", "low"),
                                    icon=ft.Icons.WAVES_ROUNDED,
                                    event_lat=float(eq.get("latitude", 0.0)),
                                    event_lon=float(eq.get("longitude", 0.0)),
                                    event_url=eq.get("url", ""),
                                )
                                for eq in state.earthquakes[:12]
                            ],
                            spacing=tokens.SPACE_SM,
                        ),
                        padding=ft.Padding(
                            tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                        ),
                    )
                ]
            ),
            # Natural Disasters Feed
            SectionHeader("ACTIVE NATURAL EVENTS (NASA EONET)"),
            *(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                TelemetrySkeletonCard(height=95),
                            ],
                            spacing=tokens.SPACE_SM,
                        ),
                        padding=ft.Padding(
                            tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                        ),
                    )
                ]
                if state.is_loading and not state.disasters
                else [
                    ft.Container(
                        content=ft.Column(
                            [
                                TelemetryCard(
                                    title=dis.get("title", "Natural Event"),
                                    subtitle=f"Category: {dis.get('category_title', 'Hazard')} • {dis.get('date', '')[:10]}",
                                    value="",
                                    severity="high"
                                    if dis.get("type") == "wildfire"
                                    else "moderate",
                                    icon=ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED
                                    if dis.get("type") == "wildfire"
                                    else ft.Icons.CYCLONE_ROUNDED,
                                    event_lat=float(dis.get("latitude", 0.0)),
                                    event_lon=float(dis.get("longitude", 0.0)),
                                    event_url=dis.get("url", ""),
                                )
                                for dis in state.disasters[:8]
                            ],
                            spacing=tokens.SPACE_SM,
                        ),
                        padding=ft.Padding(
                            tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                        ),
                    )
                ]
            ),
            # AdMob Banner
            AdMobBanner(),
            ft.Container(height=tokens.SPACE_XXXL),
        ],
        spacing=0,
        expand=True,
    )
