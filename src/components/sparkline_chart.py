"""Multi-series hardware-accelerated telemetry charting components."""

from __future__ import annotations

import flet as ft
import flet_charts as fc

from core import tokens
from core.theme import AppColors


def TelemetryLineChart(
    values: list[float],
    accent_color: str = AppColors.PRIMARY,
    height: float = 120,
    curved: bool = True,
    show_points: bool = True,
) -> ft.Control:
    """Builds a hardware-accelerated trend line chart with below-line gradient."""
    if not values or len(values) < 2:
        return ft.Container(
            content=ft.Text(
                "Insufficient trend data to render chart",
                size=tokens.FONT_XS,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
            ),
            height=height,
            alignment=ft.Alignment.CENTER,
        )

    min_val = min(values)
    max_val = max(values)
    padding_y = max(0.5, (max_val - min_val) * 0.15) if max_val != min_val else 1.0

    points = [
        fc.LineChartDataPoint(
            x=float(i),
            y=float(val),
            tooltip=f"{val:.1f}",
        )
        for i, val in enumerate(values)
    ]

    line_data = fc.LineChartData(
        points=points,
        curved=curved,
        color=accent_color,
        stroke_width=2.5,
        below_line_bgcolor=ft.Colors.with_opacity(0.12, accent_color),
    )

    return ft.Container(
        content=fc.LineChart(
            data_series=[line_data],
            min_y=min_val - padding_y,
            max_y=max_val + padding_y,
            min_x=0,
            max_x=len(values) - 1,
            interactive=True,
            expand=True,
        ),
        height=height,
        padding=ft.Padding(
            tokens.SPACE_XS, tokens.SPACE_XS, tokens.SPACE_XS, tokens.SPACE_XS
        ),
    )


def PlanetaryThreatRadar(
    seismic_risk: float = 20.0,
    storm_risk: float = 30.0,
    flood_risk: float = 15.0,
    pollution_risk: float = 45.0,
    geomagnetic_risk: float = 10.0,
    height: float = 200,
) -> ft.Control:
    """Builds a 5-axis RadarChart assessing multi-hazard planetary threat distribution."""
    entries = [
        fc.RadarDataSetEntry(min(100.0, max(5.0, seismic_risk))),
        fc.RadarDataSetEntry(min(100.0, max(5.0, storm_risk))),
        fc.RadarDataSetEntry(min(100.0, max(5.0, flood_risk))),
        fc.RadarDataSetEntry(min(100.0, max(5.0, pollution_risk))),
        fc.RadarDataSetEntry(min(100.0, max(5.0, geomagnetic_risk))),
    ]

    dataset = fc.RadarDataSet(
        entries=entries,
        fill_color=ft.Colors.with_opacity(0.25, AppColors.PRIMARY),
        border_color=AppColors.PRIMARY,
        border_width=2.0,
        entry_radius=4.0,
    )

    titles = [
        fc.RadarChartTitle(text="Seismic"),
        fc.RadarChartTitle(text="Storm"),
        fc.RadarChartTitle(text="Flood"),
        fc.RadarChartTitle(text="AQI"),
        fc.RadarChartTitle(text="Solar"),
    ]

    return ft.Container(
        content=fc.RadarChart(
            data_sets=[dataset],
            titles=titles,
            radar_shape=fc.RadarShape.POLYGON,
            tick_count=3,
            interactive=True,
            expand=True,
        ),
        height=height,
        padding=tokens.SPACE_SM,
        alignment=ft.Alignment.CENTER,
    )
