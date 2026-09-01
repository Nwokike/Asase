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
from components.home.focus_banner import build_focus_banner
from components.home.hazard_filter_chips import build_hazard_filter_chips
from components.home.location_search_bar import build_location_search_bar
from components.home.summary_cards_row import build_quick_metrics_row
from components.section_header import SectionHeader
from components.skeleton_loader import TelemetrySkeletonCard
from components.telemetry_card import TelemetryCard
from core import tokens
from core.geo_utils import calculate_haversine_distance_km, format_distance
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
    focus_expanded, set_focus_expanded = ft.use_state(False)
    home_map_ref = ft.use_ref(None)

    # Keep the embedded radar centered on the active focus point
    use_map_center(home_map_ref, state.current_lat, state.current_lon, 9.0)

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
        # Auto-open the Now-Tracking summary card so the selection is obvious
        set_focus_expanded(True)

    def _on_bookmark_select(lat: float, lon: float, name: str, country: str = ""):
        if controller.select_coordinates:
            asyncio.create_task(controller.select_coordinates(lat, lon, name, country))
        set_focus_expanded(True)

    # Find closest active hazard to user (Memoized across coordinates & feeds)
    def _compute_closest_hazard():
        ch = None
        min_d = 999999.0
        for eq in state.earthquakes:
            lat = float(eq.get("latitude", 0.0))
            lon = float(eq.get("longitude", 0.0))
            d = calculate_haversine_distance_km(
                state.current_lat, state.current_lon, lat, lon
            )
            if d < min_d:
                min_d = d
                ch = (eq, d, "earthquake")

        for dis in state.disasters:
            lat = float(dis.get("latitude", 0.0))
            lon = float(dis.get("longitude", 0.0))
            d = calculate_haversine_distance_km(
                state.current_lat, state.current_lon, lat, lon
            )
            if d < min_d:
                min_d = d
                ch = (dis, d, dis.get("type", "hazard"))
        return ch

    closest_hazard = ft.use_memo(
        _compute_closest_hazard,
        [state.current_lat, state.current_lon, state.earthquakes, state.disasters],
    )

    # Filtered views based on hazard chip (Memoized)
    def _compute_filtered_events():
        flt = state.selected_hazard_type
        if flt != "all" and flt != "earthquake":
            eqs = []
        else:
            eqs = state.earthquakes
        if flt == "all":
            diss = state.disasters
        else:
            diss = [d for d in state.disasters if d.get("type") == flt]
        return eqs, diss

    filtered_eq, filtered_dis = ft.use_memo(
        _compute_filtered_events,
        [state.selected_hazard_type, state.earthquakes, state.disasters],
    )

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

    def _on_focus_pill_click(_e=None):
        if controller.open_report:
            asyncio.create_task(controller.open_report())

    # Two-state Now-Tracking banner: pill when collapsed, full summary card
    # (with the obvious "Open Full Dossier" button) when expanded.
    if closest_hazard:
        hazard_ev, hazard_dist, _htype = closest_hazard
        hazard_label = hazard_ev.get("place") or hazard_ev.get("title") or "hazard"
        hazard_short = (
            f"M{hazard_ev.get('magnitude', 0):.1f} quake"
            if hazard_ev.get("magnitude")
            else hazard_label
        )
        nearest_hazard_text = f"{hazard_short} • {format_distance(hazard_dist)}"
        hazard_color = (
            AppColors.SEVERITY_CRITICAL if hazard_dist < 150 else AppColors.WARNING
        )
    else:
        nearest_hazard_text = None
        hazard_color = AppColors.WARNING

    focus_banner = build_focus_banner(
        page,
        state.current_location_name,
        state.current_country,
        state.current_elevation,
        (state.weather_data or {}).get("current", {}).get("temperature_2m"),
        us_aqi,
        kp_val,
        nearest_hazard_text,
        hazard_color,
        focus_expanded,
        state.is_loading,
        on_toggle=lambda: set_focus_expanded(not focus_expanded),
        on_open_dossier=_on_focus_pill_click,
    )

    filter_chips = build_hazard_filter_chips(
        page, state.selected_hazard_type, _on_chip_select
    )
    bookmarks_bar = build_bookmarks_section(
        state.bookmarks,
        _on_bookmark_select,
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

    def _open_event_dossier():
        """Re-center tracking to the selected event and open the full Dossier.

        select_coordinates is awaited first so the Dossier (and its auto-AI
        briefing) mounts with fresh telemetry for the event's location.
        """
        ev = selected_event or {}
        lat = float(ev.get("latitude", 0.0))
        lon = float(ev.get("longitude", 0.0))
        name = ev.get("place") or ev.get("title") or f"Coord ({lat:.2f}, {lon:.2f})"

        async def _go():
            if controller.select_coordinates:
                await controller.select_coordinates(lat, lon, name, "")
            if controller.open_report:
                await controller.open_report()

        asyncio.create_task(_go())

    def _share_event_text(msg: str):
        if controller.share_text:
            asyncio.create_task(controller.share_text(msg, "Asase Hazard Alert"))

    content_list = ft.ListView(
        controls=[
            header_view,
            search_bar,
            filter_chips,
            focus_banner,
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
                                    on_click=lambda _, ev=eq: set_selected_event(ev),
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
                                    on_click=lambda _, ev=dis: set_selected_event(ev),
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

    # Page-level overlay stack: event cards and map markers both open the
    # detail sheet here, so it's visible no matter where in the feed you tap
    # (the old sheet only overlay the 240px mini-map region).
    return ft.Stack(
        controls=[
            content_list,
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
