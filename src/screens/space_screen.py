"""SpaceScreen — Geomagnetic Storms, Solar Radiation, and Magnetosphere Telemetry."""

from __future__ import annotations

import flet as ft
from flet import Control

from components.app_header import build_app_header
from components.section_header import SectionHeader
from components.sparkline_chart import TelemetryLineChart
from core import tokens
from core.theme import (
    AppColors,
    AppStyles,
)
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx


@ft.component
def SpaceScreen() -> Control:
    state = ft.use_context(AppStateCtx)

    sw = state.space_weather or {}
    kp = sw.get("kp_index", 0.0)
    status = sw.get("geomagnetic_status", "Quiet (Normal)")
    solar = sw.get("solar_activity", "Normal")
    raw_kp = sw.get("raw_kp", [])

    # Extract historical Kp values (handling both dict and list schemas from NOAA SWPC)
    kp_history: list[float] = []
    for item in raw_kp:
        if isinstance(item, dict):
            val = item.get("estimated_kp", item.get("kp_index"))
            if val is not None:
                try:
                    kp_history.append(float(val))
                except Exception:
                    pass
        elif isinstance(item, list) and len(item) > 1:
            try:
                kp_history.append(float(item[1]))
            except Exception:
                pass

    kp_color = (
        AppColors.SEVERITY_LOW
        if kp < 4.0
        else (AppColors.SEVERITY_MODERATE if kp < 6.0 else AppColors.SEVERITY_CRITICAL)
    )

    from flet import context as flet_context

    page = flet_context.page
    controller = ft.use_context(ControllerMethodsCtx)

    header_view = build_app_header(
        page,
        title="Magnetosphere",
        subtitle="NOAA SPACE WEATHER PREDICTION",
        on_refresh=controller.refresh_all,
        on_settings=lambda: (
            controller.navigate_tab(3) if controller.navigate_tab else None
        ),
        save_setting_fn=controller.save_setting,
    )

    return ft.ListView(
        controls=[
            header_view,
            ft.Container(height=tokens.SPACE_SM),
            # Hero Card
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.PUBLIC_ROUNDED,
                                        size=tokens.ICON_LG,
                                        color=AppColors.ATMOSPHERE,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                "Planetary Magnetosphere",
                                                size=tokens.FONT_LG,
                                                weight=ft.FontWeight.BOLD,
                                                font_family="Outfit",
                                            ),
                                            ft.Text(
                                                "NOAA Space Weather Prediction Center (SWPC)",
                                                size=tokens.FONT_XS,
                                                color=ft.Colors.ON_SURFACE_VARIANT,
                                            ),
                                        ],
                                        spacing=0,
                                        expand=True,
                                    ),
                                ],
                                spacing=tokens.SPACE_MD,
                            ),
                            ft.Container(height=tokens.SPACE_SM),
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Column(
                                            [
                                                ft.Text(
                                                    f"{kp:.1f}",
                                                    size=36,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=kp_color,
                                                    font_family="Outfit",
                                                ),
                                                ft.Text(
                                                    "KP-INDEX",
                                                    size=tokens.FONT_XXS,
                                                    weight=ft.FontWeight.W_700,
                                                    color=kp_color,
                                                ),
                                            ],
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            spacing=0,
                                        ),
                                        padding=tokens.SPACE_MD,
                                        border_radius=tokens.RADIUS_MD,
                                        bgcolor=ft.Colors.with_opacity(0.12, kp_color),
                                        border=ft.Border.all(
                                            1,
                                            ft.Colors.with_opacity(0.3, kp_color),
                                        ),
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text(
                                                status,
                                                size=tokens.FONT_MD,
                                                weight=ft.FontWeight.W_600,
                                                font_family="Outfit",
                                            ),
                                            ft.Text(
                                                "The planetary K-index quantifies disturbances in the horizontal component of Earth's magnetic field with an integer in the range 0–9.",
                                                size=tokens.FONT_XS,
                                                color=ft.Colors.ON_SURFACE_VARIANT,
                                            ),
                                        ],
                                        spacing=tokens.SPACE_XS,
                                        expand=True,
                                    ),
                                ],
                                spacing=tokens.SPACE_LG,
                            ),
                        ],
                        spacing=tokens.SPACE_SM,
                    ),
                    padding=tokens.SPACE_LG,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0
                ),
            ),
            # Planetary Kp-Index Trend Chart
            SectionHeader("KP-INDEX 12-READING PROGRESSION"),
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            ft.Text(
                                "Live Geomagnetic Activity Trend (NOAA Primary Sensor)",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                font_family="Outfit",
                            ),
                            TelemetryLineChart(
                                values=kp_history,
                                accent_color=AppColors.ATMOSPHERE,
                                height=140,
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
            SectionHeader("SPACE WEATHER INDICES"),
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            "Geomagnetic Storm Activity",
                                            size=tokens.FONT_SM,
                                            weight=ft.FontWeight.W_500,
                                        ),
                                        ft.Text(
                                            status,
                                            size=tokens.FONT_SM,
                                            weight=ft.FontWeight.BOLD,
                                            color=kp_color,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                padding=tokens.SPACE_MD,
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            "Solar Flare Activity (GOES Primary)",
                                            size=tokens.FONT_SM,
                                            weight=ft.FontWeight.W_500,
                                        ),
                                        ft.Text(
                                            solar,
                                            size=tokens.FONT_SM,
                                            weight=ft.FontWeight.BOLD,
                                            color=AppColors.PRIMARY,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                padding=tokens.SPACE_MD,
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
