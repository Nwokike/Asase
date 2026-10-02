"""Report Air Quality & Atmospheric Pollutants breakdown section."""

from __future__ import annotations

import flet as ft
import flet_charts as fc

from components.sparkline_chart import TelemetryLineChart
from core import tokens
from core.theme import AppColors, AppStyles


def _safe_pollutant(value: object) -> float | None:
    """Coerce a pollutant reading; None when missing/non-numeric.

    Missing pollutants are SKIPPED from the comparison chart, never
    zeroed — a zero bar would read as "clean air" for a dead feed.
    """
    try:
        if value is None or value == "":
            return None
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def build_pollutant_bars(
    pollutants: list[tuple[str, object, str]],
    height: float = 150.0,
) -> ft.Container | None:
    """At-a-glance pollutant comparison BarChart.

    ``pollutants``: (short label, raw value, rod color). Entries with
    missing values are skipped. Returns None when nothing is plottable.
    Pure function (no hooks) so bar construction is unit-testable.
    """
    groups: list[fc.BarChartGroup] = []
    for i, (label, raw, color) in enumerate(pollutants):
        value = _safe_pollutant(raw)
        if value is None:
            continue
        groups.append(
            fc.BarChartGroup(
                x=i,
                rods=[
                    fc.BarChartRod(
                        from_y=0,
                        to_y=max(value, 0.0),
                        color=color,
                        width=22,
                        border_radius=tokens.RADIUS_XS,
                        tooltip=f"{label}: {value:g} µg/m³",
                    )
                ],
            )
        )
    if not groups:
        return None
    bottom_labels = [
        fc.ChartAxisLabel(value=g.x, label=pollutants[g.x][0]) for g in groups
    ]
    return ft.Container(
        content=fc.BarChart(
            groups=groups,
            bottom_axis=fc.ChartAxis(
                show_labels=True,
                labels=bottom_labels,
                label_size=20,
            ),
            left_axis=fc.ChartAxis(show_labels=False),
            interactive=True,
            expand=True,
        ),
        height=height,
        padding=tokens.SPACE_XS,
    )


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
                    *(
                        [
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(
                                    tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                                ),
                            ),
                            build_report_metric_row(
                                "Pollutant Comparison",
                                "µg/m³ · hover bars for values",
                                "At-a-glance mix (skips dead feeds)",
                                ft.Icons.BAR_CHART_ROUNDED,
                            ),
                            build_pollutant_bars(
                                [
                                    ("PM2.5", pm25, AppColors.PRIMARY),
                                    ("PM10", pm10, AppColors.OCEAN),
                                    ("CO", co, AppColors.WARNING),
                                    ("NO₂", no2, AppColors.ATMOSPHERE),
                                    ("O₃", o3, AppColors.INFO),
                                    ("SO₂", so2, AppColors.ERROR),
                                    ("Dust", dust, AppColors.GREY),
                                ]
                            )
                            or ft.Container(),
                        ]
                    ),
                ],
                spacing=0,
            ),
            padding=0,
        ),
        padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM),
    )
