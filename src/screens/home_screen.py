"""HomeScreen — Real-Time Multi-Hazard Planetary Radar, Active Feeds & Bookmarks."""

from __future__ import annotations

import asyncio
import logging

import flet as ft
from flet import Control

from components.app_header import build_app_header
from components.banner_ad import AdMobBanner
from components.hazard_map import HazardMap, build_event_detail_sheet
from components.home.active_alert_banner import build_active_alert_banner
from components.home.bookmarks_section import build_bookmarks_section
from components.home.hazard_filter_chips import build_hazard_filter_chips
from components.home.location_search_bar import build_location_search_bar
from components.home.summary_cards_row import build_quick_metrics_row
from components.section_header import SectionHeader
from components.skeleton_loader import TelemetrySkeletonCard
from components.telemetry_card import TelemetryCard
from core import tokens
from core.geo_utils import calculate_haversine_distance_km
from core.theme import AppColors, is_dark_mode
from hooks.use_debounce import use_debounce
from hooks.use_map_center import use_map_center
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
    debounced_q = use_debounce(search_query, 350)
    selected_event, set_selected_event = ft.use_state(None)
    home_map_ref = ft.use_ref(None)

    # Keep the embedded radar centered on the active focus point
    use_map_center(home_map_ref, state.current_lat, state.current_lon, 4.0)

    async def _do_search(q: str):
        if len(q.strip()) >= 2:
            set_is_searching(True)
            results = await GeocodingService.search_cities(q)
            set_search_results(results)
            set_is_searching(False)
        else:
            set_search_results([])

    def _on_search_change(e):
        q = e.control.value or ""
        set_search_query(q)

    # NOTE: use_effect invokes the setup with ZERO arguments — the closure must
    # capture debounced_q itself (Flet does not pass deps to the setup fn).
    ft.use_effect(
        lambda: asyncio.create_task(_do_search(debounced_q)),
        [debounced_q],
    )

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

    # Filtered views based on hazard chip
    _filter = state.selected_hazard_type
    if _filter != "all" and _filter != "earthquake":
        filtered_eq = []
    else:
        filtered_eq = state.earthquakes
    if _filter == "all":
        filtered_dis = state.disasters
    else:
        filtered_dis = [d for d in state.disasters if d.get("type") == _filter]

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
            controller.navigate_tab(4) if controller.navigate_tab else None
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

    def _on_chip_select(key: str):
        if state.selected_hazard_type == key:
            return
        # Observable write — every subscribed screen re-renders instantly
        state.selected_hazard_type = key
        # Server-side EONET category refresh (throttled by _refresh_lock)
        if controller.refresh_all:
            asyncio.create_task(controller.refresh_all())

    # Visible focus-point pill — reassurance that a selection actually landed
    focus_pill = ft.Container(
        content=ft.Row(
            [
                ft.Icon(
                    ft.Icons.LOCATION_ON_ROUNDED,
                    size=tokens.ICON_XS,
                    color=AppColors.PRIMARY,
                ),
                ft.Text(
                    f"Tracking: {state.current_location_name}",
                    size=tokens.FONT_XS,
                    weight=ft.FontWeight.W_600,
                    color=AppColors.PRIMARY,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                ft.Icon(
                    ft.Icons.EXPAND_MORE_ROUNDED,
                    size=tokens.ICON_XS,
                    color=AppColors.PRIMARY,
                ),
            ],
            spacing=tokens.SPACE_XXS,
            tight=True,
        ),
        padding=ft.Padding(
            tokens.SPACE_MD, tokens.SPACE_XS, tokens.SPACE_MD, tokens.SPACE_XS
        ),
        border_radius=tokens.RADIUS_FULL,
        bgcolor=ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.3, AppColors.PRIMARY)),
        on_click=lambda _: controller.open_report() if controller.open_report else None,
        ink=True,
    )

    filter_chips = build_hazard_filter_chips(
        page, state.selected_hazard_type, _on_chip_select
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
            filter_chips,
            ft.Container(
                content=focus_pill,
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_XS, tokens.SPACE_LG, 0
                ),
            ),
            *([bookmarks_bar] if bookmarks_bar else []),
            *([alert_banner] if alert_banner else []),
            metrics_row,
            # Embedded Planetary Map Widget — tap markers to inspect hazards
            SectionHeader(
                "GLOBAL HAZARD RADAR",
                action_text="EXPAND MAP",
                on_action=lambda _: (
                    controller.show_map() if controller.show_map else None
                ),
            ),
            ft.Stack(
                controls=[
                    ft.Container(
                        content=HazardMap(
                            lat=state.current_lat,
                            lon=state.current_lon,
                            zoom=2.5,
                            earthquakes=state.earthquakes,
                            disasters=filtered_dis,
                            expand=False,
                            height=240,
                            is_dark=is_dark_mode(page),
                            on_marker_click=lambda ev: set_selected_event(ev),
                            map_ref=home_map_ref,
                        ),
                        padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
                    ),
                    *(
                        [
                            build_event_detail_sheet(
                                selected_event,
                                on_close=lambda: set_selected_event(None),
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
                expand=False,
                height=240,
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
                                for eq in filtered_eq[:12]
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
                                for dis in filtered_dis[:8]
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
