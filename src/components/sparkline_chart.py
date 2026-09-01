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
    tooltip_format: str = "{:.1f}",
    secondary_values: list[float] | None = None,
    secondary_color: str = AppColors.GREY,
    step_direction: float | None = None,
    bottom_labels: list[str] | None = None,
    left_axis_title: str | None = None,
) -> ft.Control:
    """Builds a hardware-accelerated trend line chart with multi-series support.

    Supports secondary baseline series (dashed line), discrete step charts
    (via `step_direction`), rich axis labeling, and custom point tooltips.
    """
    if not values:
        return ft.Container(
            content=ft.Text(
                "Awaiting telemetry stream...",
                size=tokens.FONT_XS,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
            ),
            height=height,
            alignment=ft.Alignment.CENTER,
        )

    # If only 1 value is present, extend to 2 points so LineChart can draw a steady baseline
    chart_vals = [values[0], values[0]] if len(values) == 1 else list(values)
    if secondary_values:
        chart_vals.extend(secondary_values)

    min_val = min(chart_vals)
    max_val = max(chart_vals)
    padding_y = max(0.5, (max_val - min_val) * 0.15) if max_val != min_val else 1.0

    points = [
        fc.LineChartDataPoint(
            x=float(i),
            y=float(val),
            tooltip=tooltip_format.format(val),
        )
        for i, val in enumerate(values)
    ]

    primary_data = fc.LineChartData(
        points=points,
        curved=curved if step_direction is None else False,
        color=accent_color,
        stroke_width=2.5,
        below_line_bgcolor=ft.Colors.with_opacity(0.12, accent_color),
        step_direction=step_direction,
    )

    data_series = [primary_data]

    if secondary_values:
        sec_points = [
            fc.LineChartDataPoint(
                x=float(i),
                y=float(val),
                tooltip=f"Mean: {tooltip_format.format(val)}",
            )
            for i, val in enumerate(secondary_values[: len(values)])
        ]
        sec_data = fc.LineChartData(
            points=sec_points,
            curved=curved,
            color=secondary_color,
            stroke_width=1.5,
            dash_pattern=[6, 4],
            below_line_bgcolor=None,
        )
        data_series.append(sec_data)

    bottom_axis = None
    if bottom_labels:
        axis_labels = [
            fc.ChartAxisLabel(
                value=float(i),
                label=ft.Text(
                    lbl,
                    size=9,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            )
            for i, lbl in enumerate(bottom_labels[: len(values)])
        ]
        bottom_axis = fc.ChartAxis(
            labels=axis_labels,
            show_labels=True,
            label_size=16,
        )

    left_axis = None
    if left_axis_title:
        left_axis = fc.ChartAxis(
            title=ft.Text(
                left_axis_title,
                size=9,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            title_size=16,
            show_labels=False,
        )

    return ft.Container(
        content=fc.LineChart(
            data_series=data_series,
            min_y=min_val - padding_y,
            max_y=max_val + padding_y,
            min_x=0,
            max_x=len(values) - 1,
            bottom_axis=bottom_axis,
            left_axis=left_axis,
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
