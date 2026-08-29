"""ReportScreen — Deep-dive Location Risk Dossier, Multi-Hazard Analysis & Radar Assessment."""

from __future__ import annotations

import asyncio
import logging

import flet as ft
from flet import Control

from components.section_header import SectionHeader
from components.sparkline_chart import PlanetaryThreatRadar, TelemetryLineChart
from core import tokens
from core.notify import show_snack
from core.theme import (
    AppColors,
    AppStyles,
)
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.report")


def _metric_row(
    label: str, value: str, sub: str = "", icon: ft.IconData | None = None
) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Row(
                    [
                        *(
                            [
                                ft.Icon(
                                    icon,
                                    size=tokens.ICON_SM,
                                    color=AppColors.PRIMARY,
                                )
                            ]
                            if icon
                            else []
                        ),
                        ft.Column(
                            [
                                ft.Text(
                                    label,
                                    size=tokens.FONT_SM,
                                    weight=ft.FontWeight.W_500,
                                ),
                                *(
                                    [
                                        ft.Text(
                                            sub,
                                            size=tokens.FONT_XS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        )
                                    ]
                                    if sub
                                    else []
                                ),
                            ],
                            spacing=0,
                        ),
                    ],
                    spacing=tokens.SPACE_SM,
                ),
                ft.Text(
                    value,
                    size=tokens.FONT_MD,
                    weight=ft.FontWeight.BOLD,
                    font_family="Outfit",
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        padding=ft.Padding(
            tokens.SPACE_MD, tokens.SPACE_SM, tokens.SPACE_MD, tokens.SPACE_SM
        ),
    )


@ft.component
def ReportScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    from flet import context as flet_context

    def _get_page():
        return flet_context.page

    # Extract AQI & Pollutants
    aqi_data = state.air_quality_data.get("current", {})
    us_aqi = aqi_data.get("us_aqi", 0)
    pm25 = aqi_data.get("pm2_5", 0)
    pm10 = aqi_data.get("pm10", 0)
    co = aqi_data.get("carbon_monoxide", 0)
    no2 = aqi_data.get("nitrogen_dioxide", 0)
    so2 = aqi_data.get("sulphur_dioxide", 0)
    o3 = aqi_data.get("ozone", 0)
    dust = aqi_data.get("dust", 0)

    # Extract AQI Hourly Trend (24 hours)
    hourly_aqi = state.air_quality_data.get("hourly", {}).get("us_aqi", [])
    aqi_trend = [float(v) for v in hourly_aqi if v is not None][-24:]

    # Extract GloFAS River Discharge Forecast (7 days)
    flood_daily = state.flood_data.get("daily", {})
    discharge_series = flood_daily.get("river_discharge", [])
    discharge_trend = [float(v) for v in discharge_series if v is not None]
    max_discharge = max(discharge_trend) if discharge_trend else 0.0

    # Extract Marine / Coastal Telemetry
    marine_data = state.marine_data.get("current", {})
    wave_height = marine_data.get("wave_height")
    wave_period = marine_data.get("wave_period")
    swell_height = marine_data.get("swell_wave_height")

    # Extract Weather & Storm Indicators
    weather_data = state.weather_data.get("current", {})
    temp = weather_data.get("temperature_2m", "--")
    apparent_temp = weather_data.get("apparent_temperature", "--")
    humidity = weather_data.get("relative_humidity_2m", "--")
    pressure = weather_data.get("surface_pressure", "--")
    wind_speed = weather_data.get("wind_speed_10m", "--")
    wind_gust = weather_data.get("wind_gusts_10m", "--")
    cape = weather_data.get("cape", 0)
    uv = weather_data.get("uv_index", "--")

    # Space Weather
    kp_val = state.space_weather.get("kp_index", 0.0)

    # Overall Threat Dimensions (0 - 100 for Radar Chart)
    seismic_risk_val = min(100.0, len(state.earthquakes) * 2.5)
    storm_risk_val = min(
        100.0, (float(cape or 0) / 30.0) + (float(wind_gust or 0) * 0.8)
    )
    flood_risk_val = min(100.0, float(max_discharge) * 0.15) if max_discharge else 10.0
    pollution_risk_val = min(100.0, float(us_aqi or 0) * 0.5)
    geomagnetic_risk_val = min(100.0, float(kp_val) * 11.0)

    # Overall Safety Score Computation (0 - 100)
    risk_deductions = 0
    if us_aqi and us_aqi > 50:
        risk_deductions += min(30, (us_aqi - 50) * 0.3)
    if wind_gust and isinstance(wind_gust, (int, float)) and wind_gust > 40:
        risk_deductions += min(20, (wind_gust - 40) * 0.5)
    if cape and cape > 1000:
        risk_deductions += min(20, (cape - 1000) * 0.01)
    if max_discharge and max_discharge > 500:
        risk_deductions += min(20, (max_discharge - 500) * 0.02)

    safety_score = max(10, int(100 - risk_deductions))
    score_color = (
        AppColors.SEVERITY_LOW
        if safety_score >= 80
        else (
            AppColors.SEVERITY_MODERATE
            if safety_score >= 60
            else AppColors.SEVERITY_CRITICAL
        )
    )

    # Check if bookmarked
    is_bookmarked = any(
        b.get("name") == state.current_location_name for b in state.bookmarks
    )

    def _toggle_bookmark_click(e):
        if controller.toggle_bookmark:
            loc = {
                "name": state.current_location_name,
                "latitude": state.current_lat,
                "longitude": state.current_lon,
                "country": state.current_country,
            }
            asyncio.create_task(controller.toggle_bookmark(loc))

    async def _export_dossier():
        page = _get_page()
        report_text = f"""====================================================
ASASE PLANETARY HAZARD DOSSIER
Generated: UTC Real-Time Stream
Location: {state.current_location_name}
Coordinates: {state.current_lat:.4f}° N, {state.current_lon:.4f}° E
Elevation: {int(state.current_elevation)} m
====================================================

OVERALL SAFETY INDEX: {safety_score}/100

1. AIR QUALITY & POLLUTANT TELEMETRY:
   - US AQI: {us_aqi}
   - PM2.5: {pm25} µg/m³
   - PM10: {pm10} µg/m³
   - Carbon Monoxide (CO): {co} µg/m³
   - Nitrogen Dioxide (NO2): {no2} µg/m³
   - Sulphur Dioxide (SO2): {so2} µg/m³
   - Ozone (O3): {o3} µg/m³
   - Saharan Dust: {dust} µg/m³

2. HYDROLOGY & GLOFAS RIVER DISCHARGE:
   - Max 7-Day River Discharge: {max_discharge:.1f} m³/s
   - Flood Recurrence Risk: {"Elevated Discharge" if max_discharge > 300 else "Normal Flow"}

3. MARINE & COASTAL SWELL:
   - Wave Height: {f"{wave_height} m" if wave_height is not None else "Inland / Sheltered"}
   - Wave Period: {f"{wave_period} s" if wave_period is not None else "--"}
   - Swell Wave Height: {f"{swell_height} m" if swell_height is not None else "--"}

4. ATMOSPHERIC & SEVERE CONVECTIVE STORM METRICS:
   - Temperature: {temp}°C (Apparent: {apparent_temp}°C)
   - Relative Humidity: {humidity}%
   - Surface Pressure: {pressure} hPa
   - Wind Speed: {wind_speed} km/h (Gusts: {wind_gust} km/h)
   - CAPE (Thunderstorm Potential): {cape} J/kg
   - UV Index: {uv}
====================================================
Asase Earth Intelligence © 2026 Kiri Research Labs
"""
        try:
            cb = ft.Clipboard()
            await cb.set(report_text)
            show_snack(page, "Dossier copied to clipboard!", bgcolor=AppColors.SUCCESS)
        except Exception as ex:
            logger.warning("Export dossier failed: %s", ex)
            show_snack(page, "Failed to copy dossier.", bgcolor=AppColors.ERROR)

    return ft.ListView(
        controls=[
            # Location Header Card
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(
                                                state.current_location_name,
                                                size=tokens.FONT_XL,
                                                weight=ft.FontWeight.BOLD,
                                                font_family="Outfit",
                                            ),
                                            ft.IconButton(
                                                icon=(
                                                    ft.Icons.STAR_ROUNDED
                                                    if is_bookmarked
                                                    else ft.Icons.STAR_BORDER_ROUNDED
                                                ),
                                                icon_color=(
                                                    AppColors.WARNING
                                                    if is_bookmarked
                                                    else ft.Colors.ON_SURFACE_VARIANT
                                                ),
                                                tooltip="Bookmark Location",
                                                on_click=_toggle_bookmark_click,
                                            ),
                                        ],
                                        spacing=tokens.SPACE_XS,
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
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            f"{safety_score}",
                                            size=tokens.FONT_XXL,
                                            weight=ft.FontWeight.BOLD,
                                            color=score_color,
                                            font_family="Outfit",
                                        ),
                                        ft.Text(
                                            "SAFETY SCORE",
                                            size=tokens.FONT_XXS,
                                            weight=ft.FontWeight.W_700,
                                            color=score_color,
                                        ),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=0,
                                ),
                                padding=tokens.SPACE_SM,
                                border_radius=tokens.RADIUS_MD,
                                bgcolor=ft.Colors.with_opacity(0.12, score_color),
                                border=ft.Border.all(
                                    1, ft.Colors.with_opacity(0.3, score_color)
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=tokens.SPACE_LG,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0
                ),
            ),
            # Actions
            ft.Container(
                content=ft.Row(
                    [
                        ft.FilledButton(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.COPY_ROUNDED,
                                        size=tokens.ICON_SM,
                                        color=ft.Colors.WHITE,
                                    ),
                                    ft.Text(
                                        "Copy Full Dossier",
                                        size=tokens.FONT_SM,
                                        weight=ft.FontWeight.W_600,
                                        color=ft.Colors.WHITE,
                                    ),
                                ],
                                spacing=4,
                            ),
                            style=ft.ButtonStyle(
                                bgcolor=AppColors.PRIMARY,
                                shape=ft.RoundedRectangleBorder(
                                    radius=tokens.RADIUS_MD
                                ),
                            ),
                            on_click=lambda _: asyncio.create_task(_export_dossier()),
                        ),
                        ft.OutlinedButton(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.MAP_ROUNDED, size=tokens.ICON_SM),
                                    ft.Text("View on Map", size=tokens.FONT_SM),
                                ],
                                spacing=4,
                            ),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD)
                            ),
                            on_click=lambda _: (
                                controller.show_map() if controller.show_map else None
                            ),
                        ),
                    ],
                    spacing=tokens.SPACE_MD,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0
                ),
            ),
            # Planetary Threat Radar Assessment
            SectionHeader("PLANETARY THREAT RADAR PROFILE"),
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            ft.Text(
                                "5-Axis Multi-Hazard Vulnerability Index",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                font_family="Outfit",
                            ),
                            PlanetaryThreatRadar(
                                seismic_risk=seismic_risk_val,
                                storm_risk=storm_risk_val,
                                flood_risk=flood_risk_val,
                                pollution_risk=pollution_risk_val,
                                geomagnetic_risk=geomagnetic_risk_val,
                                height=200,
                            ),
                        ],
                        spacing=tokens.SPACE_XS,
                    ),
                    padding=tokens.SPACE_MD,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            # GloFAS Hydrology & River Discharge Section
            SectionHeader("HYDROLOGY & GLOFAS RIVER DISCHARGE (7-DAY FORECAST)"),
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            _metric_row(
                                "Peak River Discharge",
                                f"{max_discharge:.1f} m³/s"
                                if max_discharge
                                else "Dry / Minor stream",
                                "GloFAS Global Hydrological Simulation",
                                ft.Icons.WATER_DAMAGE_ROUNDED,
                            ),
                            *(
                                [
                                    ft.Container(
                                        content=TelemetryLineChart(
                                            values=discharge_trend,
                                            accent_color=AppColors.OCEAN,
                                            height=110,
                                        ),
                                        padding=tokens.SPACE_XS,
                                    )
                                ]
                                if discharge_trend
                                else []
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=0,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            # Marine & Coastal Swell Section
            SectionHeader("MARINE DYNAMICS & COASTAL SWELL"),
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            _metric_row(
                                "Significant Wave Height",
                                f"{wave_height} m"
                                if wave_height is not None
                                else "Inland location (N/A)",
                                "Open-Meteo Global Marine Engine",
                                ft.Icons.SURFING_ROUNDED,
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "Swell Wave Height",
                                f"{swell_height} m"
                                if swell_height is not None
                                else "N/A",
                                f"Wave period: {wave_period}s" if wave_period else "",
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=0,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            # Air Quality Breakdown
            SectionHeader("AIR QUALITY & POLLUTANTS (OPEN-METEO AQI)"),
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            _metric_row(
                                "US Air Quality Index (AQI)",
                                f"{int(us_aqi)}",
                                "EPA Standards",
                                ft.Icons.AIR_ROUNDED,
                            ),
                            *(
                                [
                                    ft.Container(
                                        content=TelemetryLineChart(
                                            values=aqi_trend,
                                            accent_color=AppColors.PRIMARY,
                                            height=110,
                                        ),
                                        padding=tokens.SPACE_XS,
                                    )
                                ]
                                if aqi_trend
                                else []
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "Fine Particulate Matter (PM2.5)",
                                f"{pm25} µg/m³",
                                "Combustion & smoke particles",
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "Coarse Particulate Matter (PM10)",
                                f"{pm10} µg/m³",
                                "Dust, pollen, and mold spores",
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "Carbon Monoxide (CO)",
                                f"{co} µg/m³",
                                "Combustion byproduct",
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "Nitrogen Dioxide (NO2)",
                                f"{no2} µg/m³",
                                "Traffic and industrial emissions",
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "Ozone (O3)",
                                f"{o3} µg/m³",
                                "Ground-level photochemical smog",
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=0,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM
                ),
            ),
            # Atmospheric & Storm Indicators
            SectionHeader("ATMOSPHERIC DYNAMICS & CONVECTIVE STORM INDEX"),
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            _metric_row(
                                "Surface Temperature",
                                f"{temp}°C",
                                f"Feels like {apparent_temp}°C",
                                ft.Icons.THERMOSTAT_ROUNDED,
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "Peak Wind Gusts",
                                f"{wind_gust} km/h",
                                f"Sustained wind: {wind_speed} km/h",
                                ft.Icons.AIR_ROUNDED,
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "CAPE Storm Potential",
                                f"{cape} J/kg",
                                "Convective Available Potential Energy (Thunderstorm severity)",
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "Atmospheric Pressure",
                                f"{pressure} hPa",
                                "Barometric sensor reading",
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            _metric_row(
                                "Relative Humidity",
                                f"{humidity}%",
                                "Moisture saturation level",
                            ),
                        ],
                        spacing=0,
                    ),
                    padding=0,
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
