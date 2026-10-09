"""HomeScreen — Real-Time Multi-Hazard Planetary Radar, Active Feeds & Bookmarks."""

from __future__ import annotations

import logging

import flet as ft
from flet import Control

from components.adaptive_nav import window_class
from components.banner_ad import AdMobBanner
from components.empty_state import EmptyState
from components.hazard_map import (
    HazardMap,
    build_event_detail_sheet,
    build_zoom_controls,
)
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
from core.tasks import schedule
from core.theme import AppColors, is_dark_mode
from core.units import feed_age
from hooks.search_generation import SearchGeneration
from hooks.use_debounce import use_debounce
from hooks.use_map_center import use_map_center
from services.geocoding_service import GeocodingService
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.home")


def canvas_panel_widths(viewport_width: float | None) -> tuple[bool, float, float]:
    """(use_canvas, rail_width, feeds_width) for a viewport width.

    Compact windows keep the single-column scroll (no canvas). Medium
    (600-840px) computes proportional widths so panels + margins stay
    inside the viewport; expanded uses the room proportionally with
    caps — a big screen gets wide, roomy panels instead of cramped
    fixed ones (a 4K viewport caps so panels can't drift).
    """
    vw = viewport_width or 0.0
    cls = window_class(vw if vw else None)
    use_canvas = cls in ("medium", "expanded")
    if cls == "medium" and vw:
        rail_w = min(320.0, vw * 0.45)
        feeds_w = max(260.0, vw - rail_w - 2 * tokens.SPACE_MD - 8)
    else:
        rail_w = max(360.0, min(440.0, vw * 0.26))
        feeds_w = max(420.0, min(560.0, vw * 0.34))
    return use_canvas, rail_w, feeds_w


@ft.component
def HomeScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    from flet import context as flet_context

    page = flet_context.page

    search_query, set_search_query = ft.use_state("")
    search_results, set_search_results = ft.use_state([])
    is_searching, set_is_searching = ft.use_state(False)
    debounced_q = use_debounce(search_query, 350)
    selected_event, set_selected_event = ft.use_state(None)
    focus_expanded, set_focus_expanded = ft.use_state(False)
    home_map_ref = ft.use_ref(None)
    # Generation counter: overlapping debounced searches resolve out of
    # order — only the latest generation may publish its results.
    search_generation = ft.use_ref(SearchGeneration)

    # Keep the embedded radar centered on the active focus point
    use_map_center(home_map_ref, state.current_lat, state.current_lon, 9.0)

    async def _do_search(q: str):
        gen = search_generation.current
        token = gen.begin()
        if len(q.strip()) < 2:
            set_search_results([])
            set_is_searching(False)
            return
        set_is_searching(True)
        results = await GeocodingService.search_cities(q)
        # A newer search started while we were in flight — drop our stale
        # results; the newer generation owns the spinner and the list.
        if gen.is_current(token):
            set_search_results(results)
            set_is_searching(False)

    def _on_search_change(e):
        q = e.control.value or ""
        set_search_query(q)

    # NOTE: use_effect invokes the setup with ZERO arguments — the closure must
    # capture debounced_q itself (Flet does not pass deps to the setup fn).
    ft.use_effect(
        lambda: schedule(_do_search, debounced_q, page=page),
        [debounced_q],
    )

    def _select_city(city: dict):
        if controller.select_coordinates:
            schedule(
                controller.select_coordinates,
                city["latitude"],
                city["longitude"],
                city["name"],
                city.get("country", ""),
                page=page,
            )
        set_search_query("")
        set_search_results([])
        # Auto-open the Now-Tracking summary card so the selection is obvious
        set_focus_expanded(True)

    def _on_bookmark_select(lat: float, lon: float, name: str, country: str = ""):
        if controller.select_coordinates:
            schedule(controller.select_coordinates, lat, lon, name, country, page=page)
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

    search_bar = build_location_search_bar(
        page,
        search_query,
        search_results,
        _on_search_change,
        _select_city,
        controller.locate_user,
        is_searching=is_searching,
    )

    def _on_chip_select(key: str):
        if state.selected_hazard_type == key:
            return
        # Observable write — every subscribed screen re-renders instantly
        state.selected_hazard_type = key
        # Server-side EONET category refresh (throttled by _refresh_lock)
        if controller.refresh_all:
            schedule(controller.refresh_all, page=page)

    def _on_focus_pill_click(_e=None):
        if controller.open_report:
            schedule(controller.open_report, page=page)

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

        schedule(_go, page=page)

    def _share_event_text(msg: str):
        if controller.share_text:
            schedule(controller.share_text, msg, "Asase Hazard Alert", page=page)

    # Canvas mode decision first — the map's zoom-control placement and the
    # rail contents depend on it.
    try:
        _vw = float(page.width) if page and page.width else 0.0
    except (TypeError, ValueError):
        _vw = 0.0
    use_canvas, _rail_w, _feeds_w = canvas_panel_widths(_vw)

    map_widget = HazardMap(
        lat=state.current_lat,
        lon=state.current_lon,
        zoom=2.5,
        earthquakes=state.earthquakes,
        disasters=filtered_dis,
        expand=True,
        is_dark=is_dark_mode(page),
        on_marker_click=lambda ev: set_selected_event(ev),
        map_ref=home_map_ref,
        # Canvas mode gets the pill inside the rail (a pill floating over
        # the map itself is unclickable on home — the search rail and feeds
        # panel cover it, and medium's inter-panel gap is 8px at every
        # width). The compact mini-map keeps the floating top-left pill.
        zoom_placement="none" if use_canvas else "top-left",
    )

    map_header = SectionHeader(
        "GLOBAL HAZARD RADAR",
        action_text="EXPAND MAP",
        on_action=lambda _: controller.show_map() if controller.show_map else None,
    )

    content_list = ft.ListView(
        controls=[
            search_bar,
            filter_chips,
            focus_banner,
            *([bookmarks_bar] if bookmarks_bar else []),
            *([alert_banner] if alert_banner else []),
            metrics_row,
            # Embedded Planetary Map Widget — tap markers to inspect hazards
            *(
                [map_header]
                if not use_canvas
                else [
                    ft.Container(
                        content=map_header,
                        padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
                        bgcolor=ft.Colors.with_opacity(
                            0.85, AppColors.get_surface(page)
                        ),
                    )
                ]
            ),
            *(
                [
                    ft.Stack(
                        controls=[
                            ft.Container(
                                content=map_widget,
                                padding=ft.Padding(
                                    tokens.SPACE_LG, 0, tokens.SPACE_LG, 0
                                ),
                            ),
                        ],
                        expand=False,
                        height=240,
                    )
                ]
                if not use_canvas
                else []
            ),
            # Real-Time Seismic Stream
            SectionHeader(
                f"RECENT SEISMIC ACTIVITY (USGS 24H • {feed_age('usgs')})",
            ),
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
                            ]
                            if filtered_eq
                            else [
                                EmptyState(
                                    icon=ft.Icons.WAVES_ROUNDED,
                                    title="No quakes in range",
                                    subtitle="Nothing above your magnitude filter in the last 24h.",
                                )
                            ],
                            spacing=tokens.SPACE_SM,
                        ),
                        padding=ft.Padding(
                            tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                        ),
                    )
                ]
            ),
            SectionHeader(
                f"ACTIVE NATURAL EVENTS (NASA EONET • {feed_age('eonet')})",
            ),
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
                            ]
                            if filtered_dis
                            else [
                                EmptyState(
                                    icon=ft.Icons.ECO_ROUNDED,
                                    title="No active events",
                                    subtitle="No open EONET events match this filter right now.",
                                )
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
    sheet = (
        [
            build_event_detail_sheet(
                selected_event,
                on_close=lambda: set_selected_event(None),
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
    )
    if not use_canvas:
        return ft.Stack(
            controls=[content_list, *sheet],
            expand=True,
        )
    # Full-bleed canvas: map background, floating control rail on the left,
    # scrollable feed column as a translucent right panel.
    # The SAME pill the full map screen uses — position is the only
    # change: bottom-left inside the rail's own box, where the search
    # bar, the feeds panel and the event sheet can never cover it.
    # (A pill floating over the map itself can't work on home: medium's
    # inter-panel gap is exactly 8px at every width.)
    rail_zoom = build_zoom_controls(home_map_ref, page=page, is_dark=is_dark_mode(page))
    rail_zoom.bottom = tokens.SPACE_MD
    rail_zoom.left = tokens.SPACE_MD

    left_rail = ft.Container(
        content=ft.Stack(
            controls=[
                ft.Column(
                    [search_bar, filter_chips, focus_banner],
                    spacing=tokens.SPACE_SM,
                    scroll=ft.ScrollMode.AUTO,
                ),
                rail_zoom,
            ],
            expand=True,
        ),
        width=_rail_w,
        padding=ft.Padding(tokens.SPACE_MD, tokens.SPACE_MD, 0, tokens.SPACE_MD),
        top=tokens.SPACE_MD,
        left=tokens.SPACE_MD,
        bottom=tokens.SPACE_MD,
    )
    right_feeds = ft.Container(
        content=ft.ListView(
            controls=[
                *([bookmarks_bar] if bookmarks_bar else []),
                *([alert_banner] if alert_banner else []),
                metrics_row,
                ft.Container(
                    content=map_header,
                    padding=ft.Padding(0, tokens.SPACE_MD, 0, 0),
                ),
                SectionHeader(
                    f"RECENT SEISMIC ACTIVITY (USGS 24H • {feed_age('usgs')})",
                ),
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
                                        on_click=lambda _, ev=eq: set_selected_event(
                                            ev
                                        ),
                                    )
                                    for eq in filtered_eq[:12]
                                ]
                                if filtered_eq
                                else [
                                    EmptyState(
                                        icon=ft.Icons.WAVES_ROUNDED,
                                        title="No quakes in range",
                                        subtitle="Nothing above your magnitude filter in the last 24h.",
                                    )
                                ],
                                spacing=tokens.SPACE_SM,
                            ),
                        )
                    ]
                ),
                SectionHeader(
                    f"ACTIVE NATURAL EVENTS (NASA EONET • {feed_age('eonet')})",
                ),
                *(
                    [
                        ft.Container(
                            content=ft.Column(
                                [TelemetrySkeletonCard(height=95)],
                                spacing=tokens.SPACE_SM,
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
                                        on_click=lambda _, ev=dis: set_selected_event(
                                            ev
                                        ),
                                    )
                                    for dis in filtered_dis[:8]
                                ]
                                if filtered_dis
                                else [
                                    EmptyState(
                                        icon=ft.Icons.ECO_ROUNDED,
                                        title="No active events",
                                        subtitle="No open EONET events match this filter right now.",
                                    )
                                ],
                                spacing=tokens.SPACE_SM,
                            ),
                        )
                    ]
                ),
                AdMobBanner(),
                ft.Container(height=tokens.SPACE_XXXL),
            ],
            spacing=0,
            expand=True,
        ),
        width=_feeds_w,
        bgcolor=ft.Colors.with_opacity(0.92, AppColors.get_surface(page)),
        border_radius=tokens.RADIUS_LG,
        padding=ft.Padding(tokens.SPACE_MD, tokens.SPACE_MD, tokens.SPACE_MD, 0),
        top=tokens.SPACE_MD,
        right=tokens.SPACE_MD,
        bottom=tokens.SPACE_MD,
    )
    return ft.Stack(
        controls=[map_widget, left_rail, right_feeds, *sheet],
        expand=True,
    )
