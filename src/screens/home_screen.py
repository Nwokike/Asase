"""HomeScreen — Search-first Planetary Telemetry Dashboard.

Combines Sherlock's search-first hero with live telemetry cards, interactive
map preview, quick filter chips, recent search history, and saved bookmarks.
"""

from __future__ import annotations

import asyncio
import logging

import flet as ft
from flet import Control

from components.banner_ad import build_banner_ad
from components.hazard_map import HazardMap
from components.telemetry_card import TelemetryCard
from core import tokens
from core.constants import APP_NAME, MSG_OFFLINE
from core.theme import (
    AppColors,
    AppStyles,
    is_dark_mode,
)
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
    theme_version, set_theme_version = ft.use_state(0)

    from flet import context as flet_context

    def _get_page():
        return flet_context.page

    # ── Search & Geocoding Logic ──

    def _on_search_query_change(val: str):
        set_search_query(val)
        if len(val.strip()) >= 2:
            set_is_searching(True)

            async def _do_search():
                from services.geocoding_service import GeocodingService

                cities = await GeocodingService.search_cities(val)
                set_search_results(cities)
                set_is_searching(False)

            asyncio.create_task(_do_search())
        else:
            set_search_results([])
            set_is_searching(False)

    def _select_city(city: dict):
        lat = city["latitude"]
        lon = city["longitude"]
        name = f"{city['name']}, {city.get('country', '')}"
        set_search_query("")
        set_search_results([])
        if controller.select_coordinates:
            asyncio.create_task(
                controller.select_coordinates(lat, lon, name, city.get("country", ""))
            )

    def _on_paste(e):
        async def _paste():
            try:
                cb = ft.Clipboard()
                text = await cb.get()
                if text:
                    _on_search_query_change(text.strip())
            except Exception:
                pass

        asyncio.create_task(_paste())

    # ── Theme Toggle ──

    def _toggle_theme(e):
        page = _get_page()
        if page.theme_mode == ft.ThemeMode.DARK:
            new_mode = ft.ThemeMode.LIGHT
            mode_str = "light"
        elif page.theme_mode == ft.ThemeMode.LIGHT:
            new_mode = ft.ThemeMode.SYSTEM
            mode_str = "system"
        else:
            new_mode = ft.ThemeMode.DARK
            mode_str = "dark"

        page.theme_mode = new_mode
        state.theme_mode = new_mode
        set_theme_version(theme_version + 1)
        if controller.save_setting:
            asyncio.create_task(controller.save_setting("asase.theme", mode_str))

    def _get_theme_icon():
        page = _get_page()
        if page.theme_mode == ft.ThemeMode.DARK:
            return ft.Icons.DARK_MODE_ROUNDED
        elif page.theme_mode == ft.ThemeMode.LIGHT:
            return ft.Icons.LIGHT_MODE_ROUNDED
        return ft.Icons.SETTINGS_SYSTEM_DAYDREAM_ROUNDED

    # ── Bookmark Handler ──

    is_bookmarked = any(
        b.get("name") == state.current_location_name for b in state.bookmarks
    )

    def _toggle_bookmark(e):
        if controller.toggle_bookmark:
            loc = {
                "name": state.current_location_name,
                "latitude": state.current_lat,
                "longitude": state.current_lon,
                "country": state.current_country,
            }
            asyncio.create_task(controller.toggle_bookmark(loc))

    # ── Computed Telemetry Summary ──

    aqi_current = state.air_quality_data.get("current", {})
    us_aqi = aqi_current.get("us_aqi")
    aqi_val_str = f"{int(us_aqi)}" if us_aqi is not None else "--"
    aqi_sev = (
        "low"
        if us_aqi and us_aqi <= 50
        else (
            "moderate"
            if us_aqi and us_aqi <= 100
            else ("high" if us_aqi and us_aqi <= 150 else "critical")
        )
    )

    weather_curr = state.weather_data.get("current", {})
    temp = weather_curr.get("temperature_2m")
    temp_str = f"{temp}°C" if temp is not None else "--"
    wind_gust = weather_curr.get("wind_gusts_10m")
    wind_str = f"{wind_gust} km/h" if wind_gust is not None else "--"

    # River Discharge Max
    flood_daily = state.flood_data.get("daily", {})
    discharge_series = flood_daily.get("river_discharge", [])
    max_discharge = max([v for v in discharge_series if v is not None], default=0.0)

    # Marine Swell
    marine_data = state.marine_data.get("current", {})
    wave_height = marine_data.get("wave_height")

    eq_count = len(state.earthquakes)
    is_dark = is_dark_mode(_get_page())

    # ── Search Suggestions / Recent Searches Dropdown ──

    search_suggestions = []
    if search_results:
        for c in search_results[:5]:
            search_suggestions.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.LOCATION_CITY_ROUNDED,
                                size=tokens.ICON_SM,
                                color=AppColors.PRIMARY,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        f"{c['name']}, {c.get('admin1', '')}",
                                        size=tokens.FONT_SM,
                                        weight=ft.FontWeight.W_600,
                                    ),
                                    ft.Text(
                                        f"{c.get('country', '')} • Elev: {int(c.get('elevation', 0))}m",
                                        size=tokens.FONT_XS,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                            ft.Icon(
                                ft.Icons.NORTH_WEST_ROUNDED,
                                size=tokens.ICON_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=tokens.SPACE_MD,
                    ),
                    padding=tokens.SPACE_SM,
                    border_radius=tokens.RADIUS_MD,
                    bgcolor=ft.Colors.with_opacity(
                        0.08, AppColors.PRIMARY if is_dark else ft.Colors.BLACK
                    ),
                    ink=True,
                    on_click=lambda _, city=c: _select_city(city),
                )
            )

    # ── Saved Bookmarks & Recent Locations Chips ──

    saved_chips = []
    for b in state.bookmarks[:6]:
        saved_chips.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.STAR_ROUNDED, size=14, color=AppColors.WARNING
                        ),
                        ft.Text(
                            b.get("name", "Saved").split(",")[0],
                            size=tokens.FONT_XS,
                            weight=ft.FontWeight.W_600,
                        ),
                    ],
                    spacing=4,
                    tight=True,
                ),
                padding=ft.Padding(10, 6, 10, 6),
                border_radius=tokens.RADIUS_FULL,
                bgcolor=ft.Colors.with_opacity(0.12, AppColors.WARNING),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.3, AppColors.WARNING)),
                on_click=lambda _, city=b: _select_city(city),
            )
        )

    # ── Telemetry Grid (Responsive 4-col / 2-col) ──

    telemetry_cards = [
        ft.Container(
            content=TelemetryCard(
                icon=ft.Icons.AIR_ROUNDED,
                title="Air Quality (US AQI)",
                value=aqi_val_str,
                subtitle=f"PM2.5: {aqi_current.get('pm2_5', '--')} µg/m³ • Dust: {aqi_current.get('dust', '--')}",
                severity=aqi_sev,
                accent_color=AppColors.PRIMARY,
                on_click=lambda _: (
                    controller.show_report() if controller.show_report else None
                ),
            ),
            col={"sm": 12, "md": 6, "lg": 3},
        ),
        ft.Container(
            content=TelemetryCard(
                icon=ft.Icons.WATER_DAMAGE_ROUNDED,
                title="River Discharge (GloFAS)",
                value=f"{max_discharge:.1f} m³/s" if max_discharge else "Dry / Normal",
                subtitle="GloFAS 10-day global hydrological modeling",
                severity="moderate" if max_discharge > 300 else "low",
                accent_color=AppColors.OCEAN,
                on_click=lambda _: (
                    controller.show_report() if controller.show_report else None
                ),
            ),
            col={"sm": 12, "md": 6, "lg": 3},
        ),
        ft.Container(
            content=TelemetryCard(
                icon=ft.Icons.WAVES_ROUNDED,
                title="Active Earthquakes",
                value=f"{eq_count} Events",
                subtitle="USGS Real-time global seismic sensors",
                severity="moderate" if eq_count > 10 else "low",
                accent_color=AppColors.SEVERITY_HIGH,
                on_click=lambda _: (
                    controller.show_map() if controller.show_map else None
                ),
            ),
            col={"sm": 12, "md": 6, "lg": 3},
        ),
        ft.Container(
            content=TelemetryCard(
                icon=ft.Icons.WB_SUNNY_ROUNDED,
                title="Atmospheric Dynamics",
                value=temp_str,
                subtitle=f"Wind Gusts: {wind_str} • Wave: {f'{wave_height}m' if wave_height is not None else 'Inland'}",
                severity="low",
                accent_color=AppColors.OCEAN_LIGHT,
                on_click=lambda _: (
                    controller.show_report() if controller.show_report else None
                ),
            ),
            col={"sm": 12, "md": 6, "lg": 3},
        ),
    ]

    # ── Assemble Dashboard ──

    return ft.ListView(
        controls=[
            # Header
            ft.Container(
                content=ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Image(src="icon.png", width=30, height=30),
                                ft.Text(
                                    APP_NAME,
                                    size=tokens.FONT_LG,
                                    weight=ft.FontWeight.BOLD,
                                    font_family="Outfit",
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        "GLOBAL DEFENSE",
                                        size=tokens.FONT_XXS,
                                        weight=ft.FontWeight.W_700,
                                        color=AppColors.PRIMARY,
                                    ),
                                    padding=ft.Padding(6, 2, 6, 2),
                                    border_radius=tokens.RADIUS_SM,
                                    bgcolor=ft.Colors.with_opacity(
                                        0.12, AppColors.PRIMARY
                                    ),
                                ),
                            ],
                            spacing=tokens.SPACE_SM,
                        ),
                        ft.Row(
                            [
                                ft.IconButton(
                                    icon=ft.Icons.MY_LOCATION_ROUNDED,
                                    icon_size=20,
                                    tooltip="Locate My GPS",
                                    on_click=lambda _: (
                                        asyncio.create_task(controller.locate_user())
                                        if controller.locate_user
                                        else None
                                    ),
                                ),
                                ft.IconButton(
                                    icon=_get_theme_icon(),
                                    icon_size=20,
                                    tooltip="Toggle Theme",
                                    on_click=_toggle_theme,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.SETTINGS_ROUNDED,
                                    icon_size=20,
                                    tooltip="Settings",
                                    on_click=lambda _: (
                                        controller.show_settings()
                                        if controller.show_settings
                                        else None
                                    ),
                                ),
                            ],
                            spacing=0,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0
                ),
            ),
            # Offline Banner
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.WIFI_OFF_ROUNDED,
                            color=ft.Colors.ON_ERROR_CONTAINER,
                            size=tokens.ICON_SM,
                        ),
                        ft.Text(
                            MSG_OFFLINE,
                            size=tokens.FONT_XS,
                            color=ft.Colors.ON_ERROR_CONTAINER,
                            expand=True,
                        ),
                    ],
                    spacing=tokens.SPACE_SM,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, tokens.SPACE_SM
                ),
                bgcolor=ft.Colors.ERROR_CONTAINER,
                visible=not state.is_online,
            ),
            # Search Bar
            ft.Container(
                content=ft.Column(
                    [
                        ft.TextField(
                            value=search_query,
                            hint_text="Search any global city, coordinate, or region...",
                            prefix_icon=ft.Icons.SEARCH_ROUNDED,
                            suffix=ft.IconButton(
                                icon=ft.Icons.PASTE_ROUNDED,
                                icon_size=18,
                                icon_color=AppColors.PRIMARY,
                                tooltip="Paste from clipboard",
                                on_click=_on_paste,
                            ),
                            border_radius=tokens.RADIUS_MD,
                            text_size=tokens.FONT_MD,
                            filled=True,
                            bgcolor=(
                                AppColors.DARK_SURFACE
                                if is_dark
                                else AppColors.LIGHT_SURFACE
                            ),
                            border_color=ft.Colors.with_opacity(
                                0.15,
                                (
                                    AppColors.DARK_TEXT
                                    if is_dark
                                    else AppColors.LIGHT_TEXT
                                ),
                            ),
                            on_change=lambda e: _on_search_query_change(
                                e.control.value
                            ),
                        ),
                        *(
                            [
                                ft.Container(
                                    content=ft.Column(
                                        search_suggestions, spacing=tokens.SPACE_XS
                                    ),
                                    padding=tokens.SPACE_SM,
                                    border_radius=tokens.RADIUS_MD,
                                    bgcolor=(
                                        AppColors.DARK_SURFACE_2
                                        if is_dark
                                        else AppColors.LIGHT_SURFACE_2
                                    ),
                                    border=ft.Border.all(
                                        1,
                                        ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
                                    ),
                                )
                            ]
                            if search_suggestions
                            else []
                        ),
                    ],
                    spacing=tokens.SPACE_XS,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            # Saved Bookmarks Bar (if any saved)
            *(
                [
                    ft.Container(
                        content=ft.Row(
                            saved_chips,
                            scroll=ft.ScrollMode.AUTO,
                            spacing=tokens.SPACE_SM,
                        ),
                        padding=ft.Padding(
                            tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                        ),
                    )
                ]
                if saved_chips
                else []
            ),
            # Active Location Focus Card
            ft.Container(
                content=ft.Row(
                    [
                        ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(
                                            ft.Icons.LOCATION_ON_ROUNDED,
                                            size=tokens.ICON_SM,
                                            color=AppColors.PRIMARY,
                                        ),
                                        ft.Text(
                                            state.current_location_name,
                                            size=tokens.FONT_LG,
                                            weight=ft.FontWeight.BOLD,
                                            font_family="Outfit",
                                        ),
                                        ft.IconButton(
                                            icon=(
                                                ft.Icons.STAR_ROUNDED
                                                if is_bookmarked
                                                else ft.Icons.STAR_BORDER_ROUNDED
                                            ),
                                            icon_size=20,
                                            icon_color=(
                                                AppColors.WARNING
                                                if is_bookmarked
                                                else ft.Colors.ON_SURFACE_VARIANT
                                            ),
                                            tooltip="Bookmark Location",
                                            on_click=_toggle_bookmark,
                                        ),
                                    ],
                                    spacing=tokens.SPACE_XXS,
                                ),
                                ft.Text(
                                    f"Coordinates: {state.current_lat:.4f}° N, {state.current_lon:.4f}° E • Elevation: {int(state.current_elevation)}m",
                                    size=tokens.FONT_XS,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                    font_family="Outfit",
                                ),
                            ],
                            spacing=tokens.SPACE_XXS,
                            expand=True,
                        ),
                        ft.FilledButton(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.ASSESSMENT_ROUNDED,
                                        size=tokens.ICON_SM,
                                        color=ft.Colors.WHITE,
                                    ),
                                    ft.Text(
                                        "Risk Dossier",
                                        size=tokens.FONT_SM,
                                        weight=ft.FontWeight.W_600,
                                        color=ft.Colors.WHITE,
                                    ),
                                ],
                                spacing=4,
                                tight=True,
                            ),
                            style=ft.ButtonStyle(
                                bgcolor=AppColors.PRIMARY,
                                shape=ft.RoundedRectangleBorder(
                                    radius=tokens.RADIUS_MD
                                ),
                                padding=ft.Padding(12, 8, 12, 8),
                            ),
                            on_click=lambda _: (
                                controller.show_report()
                                if controller.show_report
                                else None
                            ),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            # Telemetry Grid
            ft.Container(
                content=ft.ResponsiveRow(
                    controls=telemetry_cards,
                    spacing=tokens.SPACE_MD,
                    run_spacing=tokens.SPACE_MD,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            # Interactive Map Section
            ft.Container(
                content=ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(
                                    "PLANETARY HAZARD RADAR",
                                    size=tokens.FONT_XS,
                                    weight=ft.FontWeight.W_700,
                                    color=AppColors.PRIMARY,
                                ),
                                ft.TextButton(
                                    "Full Map",
                                    icon=ft.Icons.FULLSCREEN_ROUNDED,
                                    on_click=lambda _: (
                                        controller.show_map()
                                        if controller.show_map
                                        else None
                                    ),
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        HazardMap(
                            lat=state.current_lat,
                            lon=state.current_lon,
                            zoom=3.0,
                            earthquakes=state.earthquakes,
                            disasters=state.disasters,
                            height=260,
                            expand=False,
                        ),
                    ],
                    spacing=tokens.SPACE_XS,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            # Banner Ad placement
            build_banner_ad(_get_page()),
            # Quick Space Weather Indicator
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.PUBLIC_ROUNDED,
                                size=tokens.ICON_MD,
                                color=AppColors.ATMOSPHERE,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Magnetosphere & Space Weather",
                                        size=tokens.FONT_SM,
                                        weight=ft.FontWeight.W_600,
                                        font_family="Outfit",
                                    ),
                                    ft.Text(
                                        f"Planetary Kp-index: {state.space_weather.get('kp_index', 0.0)} • {state.space_weather.get('geomagnetic_status', 'Quiet')}",
                                        size=tokens.FONT_XS,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                        font_family="Outfit",
                                    ),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ARROW_FORWARD_ROUNDED,
                                icon_size=tokens.ICON_SM,
                                on_click=lambda _: (
                                    controller.show_space()
                                    if controller.show_space
                                    else None
                                ),
                            ),
                        ],
                        spacing=tokens.SPACE_MD,
                    ),
                    padding=tokens.SPACE_MD,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            ft.Container(height=tokens.SPACE_XXXL),
        ],
        spacing=0,
        expand=True,
    )
