"""Report Atmospheric & Convective Storm Index section."""

from __future__ import annotations

import flet as ft

from components.report.air_quality_section import build_report_metric_row
from core import tokens
from core.theme import AppStyles


def build_weather_indicators_section(
    temp: float | str,
    apparent_temp: float | str,
    wind_gust: float | str,
    wind_speed: float | str,
    cape: float | str,
    pressure: float | str,
    humidity: float | str,
) -> ft.Container:
    """Builds the Atmospheric Dynamics & Convective Storm Index card."""
    return ft.Container(
        content=AppStyles.glass_card(
            ft.Column(
                [
                    build_report_metric_row(
                        "Surface Temperature",
                        f"{temp}°C",
                        f"Feels like {apparent_temp}°C",
                        ft.Icons.THERMOSTAT_ROUNDED,
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Peak Wind Gusts",
                        f"{wind_gust} km/h",
                        f"Sustained wind: {wind_speed} km/h",
                        ft.Icons.AIR_ROUNDED,
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "CAPE Storm Potential",
                        f"{cape} J/kg",
                        "Convective Available Potential Energy (Thunderstorm severity)",
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Atmospheric Pressure",
                        f"{pressure} hPa",
                        "Barometric sensor reading",
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Relative Humidity",
                        f"{humidity}%",
                        "Moisture saturation level",
                    ),
                ],
                spacing=0,
            ),
            padding=0,
        ),
        padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM),
    )
