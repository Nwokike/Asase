"""Settings Units of Measurement section."""

from __future__ import annotations

import flet as ft

from core import tokens
from core.theme import AppStyles


def build_setting_row(
    icon: ft.IconData,
    title: str,
    subtitle: str,
    trailing: ft.Control,
) -> ft.Container:
    """Reusable standardized settings row."""
    return ft.Container(
        content=ft.Row(
            controls=[
                ft.Container(
                    content=ft.Icon(
                        icon,
                        size=tokens.ICON_MD,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    width=tokens.ICON_BACKDROP,
                    height=tokens.ICON_BACKDROP,
                    border_radius=tokens.ICON_BACKDROP_RADIUS,
                    bgcolor=ft.Colors.with_opacity(
                        tokens.OPACITY_LIGHT, ft.Colors.ON_SURFACE
                    ),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Column(
                    controls=[
                        ft.Text(title, size=tokens.FONT_MD, weight=ft.FontWeight.W_500),
                        ft.Text(
                            subtitle,
                            size=tokens.FONT_XS,
                            color=ft.Colors.with_opacity(
                                tokens.OPACITY_DIM, ft.Colors.ON_SURFACE
                            ),
                        ),
                    ],
                    spacing=tokens.SPACE_XXS,
                    expand=True,
                ),
                trailing,
            ],
            spacing=tokens.SPACE_MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(
            left=tokens.SPACE_LG,
            right=tokens.SPACE_LG,
            top=tokens.SPACE_MD,
            bottom=tokens.SPACE_MD,
        ),
    )


def build_units_section(
    temp_unit: str,
    speed_unit: str,
    on_temp_change,
    on_speed_change,
) -> ft.Container:
    """Builds the Unit Preferences card."""
    return AppStyles.glass_card(
        ft.Column(
            [
                build_setting_row(
                    ft.Icons.THERMOSTAT_ROUNDED,
                    "Temperature Unit",
                    "Choose Celsius (°C) or Fahrenheit (°F)",
                    ft.Dropdown(
                        value="Celsius" if temp_unit == "celsius" else "Fahrenheit",
                        options=[
                            ft.DropdownOption("Celsius", "Celsius (°C)"),
                            ft.DropdownOption("Fahrenheit", "Fahrenheit (°F)"),
                        ],
                        width=140,
                        height=44,
                        text_size=tokens.FONT_SM,
                        border_radius=tokens.RADIUS_SM,
                        on_select=lambda e: on_temp_change(e.control.value),
                    ),
                ),
                ft.Divider(
                    height=1,
                    color=ft.Colors.with_opacity(
                        tokens.OPACITY_SUBTLE, ft.Colors.OUTLINE
                    ),
                ),
                build_setting_row(
                    ft.Icons.SPEED_ROUNDED,
                    "Wind Speed Unit",
                    "Choose Kilometers per hour (km/h) or Miles per hour (mph)",
                    ft.Dropdown(
                        value=speed_unit if speed_unit in ("kmh", "mph") else "kmh",
                        options=[
                            ft.DropdownOption("kmh", "km/h"),
                            ft.DropdownOption("mph", "mph"),
                        ],
                        width=140,
                        height=44,
                        text_size=tokens.FONT_SM,
                        border_radius=tokens.RADIUS_SM,
                        on_select=lambda e: on_speed_change(e.control.value),
                    ),
                ),
            ],
            spacing=0,
        ),
        padding=0,
    )
