"""Report Air Quality & Atmospheric Pollutants breakdown section."""

from __future__ import annotations

import flet as ft

from components.sparkline_chart import TelemetryLineChart
from core import tokens
from core.theme import AppColors, AppStyles


def build_report_metric_row(
    label: str, value: str, sub: str = "", icon: ft.IconData | None = None
) -> ft.Container:
    """Reusable metric row for deep-dive dossiers."""
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


def build_air_quality_section(
    us_aqi: float | str,
    pm25: float | str,
    pm10: float | str,
    co: float | str,
    no2: float | str,
    o3: float | str,
    so2: float | str,
    dust: float | str,
    aqi_trend: list[float],
) -> ft.Container:
    """Builds the comprehensive Air Quality & Pollutants breakdown card."""
    return ft.Container(
        content=AppStyles.glass_card(
            ft.Column(
                [
                    build_report_metric_row(
                        "US Air Quality Index (AQI)",
                        f"{int(us_aqi)}"
                        if isinstance(us_aqi, (int, float))
                        else str(us_aqi),
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
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Fine Particulate Matter (PM2.5)",
                        f"{pm25} µg/m³",
                        "Combustion & smoke particles",
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Coarse Particulate Matter (PM10)",
                        f"{pm10} µg/m³",
                        "Dust, pollen, and mold spores",
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Carbon Monoxide (CO)",
                        f"{co} µg/m³",
                        "Combustion byproduct",
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Nitrogen Dioxide (NO2)",
                        f"{no2} µg/m³",
                        "Traffic and industrial emissions",
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Ozone (O3)",
                        f"{o3} µg/m³",
                        "Ground-level photochemical smog",
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Sulphur Dioxide (SO2)",
                        f"{so2} µg/m³",
                        "Power plants and industrial boilers",
                    ),
                    ft.Divider(
                        height=1,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                        ),
                    ),
                    build_report_metric_row(
                        "Saharan & Mineral Dust",
                        f"{dust} µg/m³",
                        "Atmospheric aerosol optical depth",
                    ),
                ],
                spacing=0,
            ),
            padding=0,
        ),
        padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM),
    )
