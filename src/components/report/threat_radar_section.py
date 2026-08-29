"""Report Threat Radar & 5-axis vulnerability section."""

from __future__ import annotations

import flet as ft

from components.sparkline_chart import PlanetaryThreatRadar
from core import tokens
from core.theme import AppStyles


def build_threat_radar_section(
    seismic_risk: float,
    storm_risk: float,
    flood_risk: float,
    pollution_risk: float,
    geomagnetic_risk: float,
) -> ft.Container:
    """Builds the 5-axis threat radar card."""
    return ft.Container(
        content=AppStyles.glass_card(
            ft.Column(
                [
                    ft.Text(
                        "5-Axis Multi-Hazard Vulnerability Index",
                        size=tokens.FONT_XS,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        font_family="Outfit",
                    ),
                    PlanetaryThreatRadar(
                        seismic_risk=seismic_risk,
                        storm_risk=storm_risk,
                        flood_risk=flood_risk,
                        pollution_risk=pollution_risk,
                        geomagnetic_risk=geomagnetic_risk,
                        height=200,
                    ),
                ],
                spacing=tokens.SPACE_XS,
            ),
            padding=tokens.SPACE_MD,
        ),
        padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_SM),
    )
