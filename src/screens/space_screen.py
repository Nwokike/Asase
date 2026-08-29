"""SpaceScreen — Geomagnetic Storms, Solar Radiation, and Magnetosphere Telemetry."""

from __future__ import annotations

import flet as ft
from flet import Control

from components.section_header import SectionHeader
from core import tokens
from core.theme import (
    AppColors,
    AppStyles,
)
from state.app_state import AppStateCtx


@ft.component
def SpaceScreen() -> Control:
    state = ft.use_context(AppStateCtx)

    sw = state.space_weather or {}
    kp = sw.get("kp_index", 0.0)
    status = sw.get("geomagnetic_status", "Quiet (Normal)")
    solar = sw.get("solar_activity", "Normal")

    kp_color = (
        AppColors.SEVERITY_LOW
        if kp < 4.0
        else (AppColors.SEVERITY_MODERATE if kp < 6.0 else AppColors.SEVERITY_CRITICAL)
    )

    return ft.ListView(
        controls=[
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
                                            1, ft.Colors.with_opacity(0.3, kp_color)
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
