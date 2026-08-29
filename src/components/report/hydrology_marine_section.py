"""Report Hydrology & Marine Dynamics sections."""

from __future__ import annotations

import flet as ft

from components.report.air_quality_section import build_report_metric_row
from components.sparkline_chart import TelemetryLineChart
from core import tokens
from core.theme import AppColors, AppStyles


def build_hydrology_section(
    max_discharge: float | None,
    discharge_trend: list[float],
) -> ft.Container:
    """Builds the GloFAS Hydrological river discharge card."""
    return ft.Container(
        content=AppStyles.glass_card(
            ft.Column(
                [
                    build_report_metric_row(
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
        padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM),
    )


def build_marine_section(
    wave_height: float | str | None,
    swell_height: float | str | None,
    wave_period: float | str | None,
) -> ft.Container:
    """Builds the Coastal Swell & Ocean Dynamics card."""
    return ft.Container(
        content=AppStyles.glass_card(
            ft.Column(
                [
                    build_report_metric_row(
                        "Significant Wave Height",
                        f"{wave_height} m"
                        if wave_height is not None
                        else "Inland location (N/A)",
                        "Open-Meteo Global Marine Engine",
                        ft.Icons.SURFING_ROUNDED,
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Swell Wave Height",
                        f"{swell_height} m" if swell_height is not None else "N/A",
                        f"Wave period: {wave_period}s" if wave_period else "",
                    ),
                ],
                spacing=0,
            ),
            padding=0,
        ),
        padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM),
    )
