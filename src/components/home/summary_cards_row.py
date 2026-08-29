"""Home planetary quick metrics row."""

from __future__ import annotations

import flet as ft

from core import tokens
from core.theme import AppColors, AppStyles


def build_quick_metrics_row(
    earthquakes_count: int,
    min_magnitude: float,
    us_aqi: str | int,
    pm25: str | float,
    kp_val: str | float,
    space_status: str,
) -> ft.Container:
    """Builds the 3-column summary metrics strip (Seismic, Air Quality, Magnetosphere)."""
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=AppStyles.glass_card(
                        ft.Column(
                            [
                                ft.Text(
                                    "USGS SEISMIC (24H)",
                                    size=tokens.FONT_XXS,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text(
                                    f"{earthquakes_count} Quakes",
                                    size=tokens.FONT_LG,
                                    weight=ft.FontWeight.BOLD,
                                    font_family="Outfit",
                                    color=AppColors.SEVERITY_HIGH,
                                ),
                                ft.Text(
                                    f"Min M{min_magnitude:.1f}+",
                                    size=tokens.FONT_XXS,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                            spacing=tokens.SPACE_XXS,
                        ),
                        padding=tokens.SPACE_MD,
                    ),
                    expand=1,
                ),
                ft.Container(
                    content=AppStyles.glass_card(
                        ft.Column(
                            [
                                ft.Text(
                                    "AIR QUALITY (AQI)",
                                    size=tokens.FONT_XXS,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text(
                                    f"{us_aqi}",
                                    size=tokens.FONT_LG,
                                    weight=ft.FontWeight.BOLD,
                                    font_family="Outfit",
                                    color=AppColors.PRIMARY,
                                ),
                                ft.Text(
                                    f"PM2.5: {pm25} µg/m³",
                                    size=tokens.FONT_XXS,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                            spacing=tokens.SPACE_XXS,
                        ),
                        padding=tokens.SPACE_MD,
                    ),
                    expand=1,
                ),
                ft.Container(
                    content=AppStyles.glass_card(
                        ft.Column(
                            [
                                ft.Text(
                                    "SPACE WEATHER (Kp)",
                                    size=tokens.FONT_XXS,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                    weight=ft.FontWeight.W_600,
                                ),
                                ft.Text(
                                    f"Kp {kp_val}",
                                    size=tokens.FONT_LG,
                                    weight=ft.FontWeight.BOLD,
                                    font_family="Outfit",
                                    color=AppColors.ATMOSPHERE,
                                ),
                                ft.Text(
                                    f"{str(space_status)[:12]}...",
                                    size=tokens.FONT_XXS,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                            spacing=tokens.SPACE_XXS,
                        ),
                        padding=tokens.SPACE_MD,
                    ),
                    expand=1,
                ),
            ],
            spacing=tokens.SPACE_SM,
        ),
        padding=ft.Padding(tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0),
    )
