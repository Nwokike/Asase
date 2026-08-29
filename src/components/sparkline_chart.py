"""Sparkline and Trend LineChart component for telemetry progression."""

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
    """Builds a lightweight, sleek trend line chart."""
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
