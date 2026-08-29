"""HomeScreen — Real-Time Multi-Hazard Planetary Radar, Active Feeds & Bookmarks."""

from __future__ import annotations

import asyncio
import logging

import flet as ft
from flet import Control

from components.banner_ad import AdMobBanner
from components.hazard_map import HazardMap
from components.section_header import SectionHeader
from components.skeleton_loader import TelemetrySkeletonCard
from components.telemetry_card import TelemetryCard
from core import tokens
from core.geo_utils import calculate_haversine_distance_km, format_distance
from core.theme import AppColors, AppStyles
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

    def _get_page():
        return page

    def _toggle_theme(e):
        p = _get_page()
        if not p:
            return
        if p.theme_mode == ft.ThemeMode.DARK:
            p.theme_mode = ft.ThemeMode.LIGHT
            mode_str = "light"
        elif p.theme_mode == ft.ThemeMode.LIGHT:
            p.theme_mode = ft.ThemeMode.SYSTEM
            mode_str = "system"
        else:
            p.theme_mode = ft.ThemeMode.DARK
            mode_str = "dark"
        state.theme_mode = p.theme_mode
        if controller.save_setting:
            asyncio.create_task(controller.save_setting("asase.theme", mode_str))
        p.update()

    def _get_theme_icon():
        p = _get_page()
        if not p or p.theme_mode == ft.ThemeMode.DARK:
            return ft.Icons.DARK_MODE_ROUNDED
        if p.theme_mode == ft.ThemeMode.LIGHT:
            return ft.Icons.LIGHT_MODE_ROUNDED
        return ft.Icons.SETTINGS_SYSTEM_DAYDREAM_ROUNDED

    header_view = ft.Container(
        content=ft.Row(
            [
                ft.Row(
                    [
                        ft.Image(
                            src="icon.png",
                            width=28,
                            height=28,
                            border_radius=6,
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    "Asase",
                                    size=tokens.FONT_MD,
                                    weight=ft.FontWeight.BOLD,
                                    font_family="Outfit",
                                ),
                                ft.Text(
                                    "EARTH INTELLIGENCE",
                                    size=8,
                                    weight=ft.FontWeight.W_700,
                                    color=AppColors.PRIMARY,
                                ),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=tokens.SPACE_XS,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=_get_theme_icon(),
                            icon_size=20,
                            tooltip="Toggle Color Mode (Dark/Light/System)",
                            on_click=_toggle_theme,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.REFRESH_ROUNDED,
                            icon_size=20,
                            tooltip="Sync Live Telemetry",
                            on_click=lambda _: (
                                asyncio.create_task(controller.refresh_all())
                                if controller.refresh_all
                                else None
                            ),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.SETTINGS_OUTLINED,
                            icon_size=20,
                            tooltip="Settings",
                            on_click=lambda _: (
                                controller.navigate_tab(3)
                                if controller.navigate_tab
                                else None
                            ),
                        ),
                    ],
                    spacing=0,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0),
    )

    return ft.ListView(
        controls=[
            header_view,
            # Top Search Bar
            ft.Container(
                content=ft.Column(
                    [
                        ft.TextField(
                            value=search_query,
                            hint_text="Search city, region, or coordinates...",
                            prefix_icon=ft.Icons.SEARCH_ROUNDED,
                            suffix=ft.IconButton(
                                icon=ft.Icons.MY_LOCATION_ROUNDED,
                                tooltip="Locate via GPS",
                                icon_color=AppColors.PRIMARY,
                                on_click=lambda _: (
                                    asyncio.create_task(controller.locate_user())
                                    if controller.locate_user
                                    else None
                                ),
                            ),
                            border_radius=tokens.RADIUS_MD,
                            filled=True,
                            bgcolor=ft.Colors.with_opacity(0.08, ft.Colors.ON_SURFACE),
                            border_color=ft.Colors.with_opacity(
                                0.15, ft.Colors.OUTLINE
                            ),
                            on_change=_on_search_change,
                            dense=True,
                        ),
                        *(
                            [
                                ft.Container(
                                    content=ft.Column(
                                        [
                                            ft.ListTile(
                                                leading=ft.Icon(
                                                    ft.Icons.LOCATION_CITY_ROUNDED,
                                                    color=AppColors.PRIMARY,
                                                ),
                                                title=ft.Text(
                                                    f"{c['name']}, {c['country']}",
                                                    weight=ft.FontWeight.W_600,
                                                ),
                                                subtitle=ft.Text(
                                                    f"Elevation: {int(c.get('elevation', 0))}m • {c.get('timezone', 'UTC')}",
                                                    size=tokens.FONT_XS,
                                                ),
                                                on_click=lambda _, city=c: _select_city(
                                                    city
                                                ),
                                            )
                                            for c in search_results
                                        ],
                                        spacing=0,
                                    ),
                                    bgcolor=AppColors.DARK_SURFACE,
                                    border_radius=tokens.RADIUS_MD,
                                    border=ft.Border.all(
                                        1,
                                        ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                                    ),
                                    shadow=ft.BoxShadow(
                                        spread_radius=2,
                                        blur_radius=10,
                                        color=ft.Colors.BLACK,
                                    ),
                                )
                            ]
                            if search_results
                            else []
                        ),
                    ],
                    spacing=tokens.SPACE_XS,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_MD, tokens.SPACE_LG, 0
                ),
            ),
            # Saved Bookmarks Chips Bar
            *(
                [
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(
                                    ft.Icons.BOOKMARK_ROUNDED,
                                    size=14,
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
                                            padding=ft.Padding(8, 4, 8, 4),
                                            border_radius=tokens.RADIUS_FULL,
                                            bgcolor=ft.Colors.with_opacity(
                                                0.12, AppColors.WARNING
                                            ),
                                            border=ft.Border.all(
                                                1,
                                                ft.Colors.with_opacity(
                                                    0.25, AppColors.WARNING
                                                ),
                                            ),
                                            on_click=lambda _, loc=b: (
                                                asyncio.create_task(
                                                    controller.select_coordinates(
                                                        loc["latitude"],
                                                        loc["longitude"],
                                                        loc["name"],
                                                        loc.get("country", ""),
                                                    )
                                                )
                                                if controller.select_coordinates
                                                else None
                                            ),
                                        )
                                        for b in state.bookmarks
                                    ]
                                ),
                            ],
                            spacing=tokens.SPACE_XS,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                        padding=ft.Padding(
                            tokens.SPACE_LG, tokens.SPACE_XS, tokens.SPACE_LG, 0
                        ),
                    )
                ]
                if state.bookmarks
                else []
            ),
            # Closest Threat Warning Banner (if within 500km)
            *(
                [
                    ft.Container(
                        content=AppStyles.glass_card(
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.WARNING_ROUNDED,
                                        color=AppColors.SEVERITY_HIGH,
                                        size=tokens.ICON_MD,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                "PROXIMITY WARNING: ACTIVE HAZARD",
                                                size=tokens.FONT_XXS,
                                                weight=ft.FontWeight.BOLD,
                                                color=AppColors.SEVERITY_HIGH,
                                            ),
                                            ft.Text(
                                                f"{closest_hazard[0].get('title', 'Hazard')} ({format_distance(closest_hazard[1])})",
                                                size=tokens.FONT_SM,
                                                weight=ft.FontWeight.W_600,
                                                max_lines=1,
                                                overflow=ft.TextOverflow.ELLIPSIS,
                                            ),
                                        ],
                                        spacing=0,
                                        expand=True,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                                        icon_size=14,
                                        on_click=lambda _: (
                                            controller.show_map()
                                            if controller.show_map
                                            else None
                                        ),
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            ),
                            padding=tokens.SPACE_MD,
                            border_color=ft.Colors.with_opacity(
                                0.4, AppColors.SEVERITY_HIGH
                            ),
                        ),
                        padding=ft.Padding(
                            tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0
                        ),
                    )
                ]
                if closest_hazard and closest_hazard[1] <= 500.0
                else []
            ),
            # Global Quick Metrics Strip
            ft.Container(
                content=ft.Row(
                    [
                        ft.Container(
                            content=AppStyles.glass_card(
                                ft.Column(
                                    [
                                        ft.Text(
                                            "USGS SEISMIC (24H)",
                                            size=tokens.FONT_XXS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                        ft.Text(
                                            f"{len(state.earthquakes)} Quakes",
                                            size=tokens.FONT_LG,
                                            weight=ft.FontWeight.BOLD,
                                            font_family="Outfit",
                                            color=AppColors.SEVERITY_HIGH,
                                        ),
                                        ft.Text(
                                            f"Min M{state.min_magnitude_filter:.1f}+",
                                            size=tokens.FONT_XXS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                    spacing=tokens.SPACE_XXS,
                                ),
                                padding=tokens.SPACE_MD,
                            ),
                            expand=1,
                        ),
                        ft.Container(
                            content=AppStyles.glass_card(
                                ft.Column(
                                    [
                                        ft.Text(
                                            "AIR QUALITY (AQI)",
                                            size=tokens.FONT_XXS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                        ft.Text(
                                            f"{us_aqi}",
                                            size=tokens.FONT_LG,
                                            weight=ft.FontWeight.BOLD,
                                            font_family="Outfit",
                                            color=AppColors.PRIMARY,
                                        ),
                                        ft.Text(
                                            f"PM2.5: {pm25} µg/m³",
                                            size=tokens.FONT_XXS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                    spacing=tokens.SPACE_XXS,
                                ),
                                padding=tokens.SPACE_MD,
                            ),
                            expand=1,
                        ),
                        ft.Container(
                            content=AppStyles.glass_card(
                                ft.Column(
                                    [
                                        ft.Text(
                                            "SPACE WEATHER (Kp)",
                                            size=tokens.FONT_XXS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                            weight=ft.FontWeight.W_600,
                                        ),
                                        ft.Text(
                                            f"Kp {kp_val}",
                                            size=tokens.FONT_LG,
                                            weight=ft.FontWeight.BOLD,
                                            font_family="Outfit",
                                            color=AppColors.ATMOSPHERE,
                                        ),
                                        ft.Text(
                                            f"{space_status[:12]}...",
                                            size=tokens.FONT_XXS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                    spacing=tokens.SPACE_XXS,
                                ),
                                padding=tokens.SPACE_MD,
                            ),
                            expand=1,
                        ),
                    ],
                    spacing=tokens.SPACE_SM,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0
                ),
            ),
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
