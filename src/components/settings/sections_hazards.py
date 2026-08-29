"""Settings Seismic & Hazards telemetry configuration section."""

from __future__ import annotations

import flet as ft

from components.settings.sections_units import build_setting_row
from core import tokens
from core.theme import AppColors, AppStyles


def build_hazards_section(
    min_magnitude: float,
    on_magnitude_change,
    on_clear_history,
) -> tuple[ft.Container, ft.Container]:
    """Builds Telemetry Thresholds card and Storage Management card."""
    telemetry_card = AppStyles.glass_card(
        ft.Column(
            [
                build_setting_row(
                    ft.Icons.WAVES_ROUNDED,
                    "Min Seismic Magnitude",
                    "Filter out minor tremors below this Richter scale threshold",
                    ft.Dropdown(
                        value=f"{min_magnitude:.1f}",
                        options=[
                            ft.DropdownOption("1.0", "M1.0+ (Micro)"),
                            ft.DropdownOption("2.5", "M2.5+ (Minor)"),
                            ft.DropdownOption("4.5", "M4.5+ (Moderate)"),
                            ft.DropdownOption("6.0", "M6.0+ (Major)"),
                        ],
                        width=140,
                        height=44,
                        text_size=tokens.FONT_SM,
                        border_radius=tokens.RADIUS_SM,
                        on_select=lambda e: on_magnitude_change(e.control.value),
                    ),
                ),
            ],
            spacing=0,
        ),
        padding=0,
    )

    data_card = AppStyles.glass_card(
        ft.Column(
            [
                build_setting_row(
                    ft.Icons.DELETE_SWEEP_ROUNDED,
                    "Clear Search History",
                    "Delete all saved recent search locations",
                    ft.OutlinedButton(
                        "Clear",
                        style=ft.ButtonStyle(color=AppColors.ERROR),
                        on_click=lambda _: on_clear_history(),
                    ),
                ),
            ],
            spacing=0,
        ),
        padding=0,
    )

    return telemetry_card, data_card
