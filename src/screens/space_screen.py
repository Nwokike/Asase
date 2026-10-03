"""SpaceScreen — Geomagnetic Storms, Solar Radiation, and Magnetosphere Telemetry."""

from __future__ import annotations

import logging

import flet as ft
from flet import Control

from components.banner_ad import build_banner_ad
from components.section_header import SectionHeader
from components.sparkline_chart import TelemetryLineChart
from core import tokens
from core.theme import (
    AppColors,
    AppStyles,
)
from state.app_state import AppStateCtx

logger = logging.getLogger("asase.space")


def g_level_from_kp(kp: float) -> int:
    """Map Kp to the NOAA G-scale storm level (0–5)."""
    if kp >= 9.0:
        return 5
    if kp >= 8.0:
        return 4
    if kp >= 7.0:
        return 3
    if kp >= 6.0:
        return 2
    if kp >= 5.0:
        return 1
    return 0


def kp_severity_color(kp: float) -> str:
    """Green → amber → red severity color for a Kp value."""
    if kp < 4.0:
        return AppColors.SEVERITY_LOW
    if kp < 6.0:
        return AppColors.SEVERITY_MODERATE
    return AppColors.SEVERITY_CRITICAL


def build_g_scale_meter(level: int) -> ft.Control:
    """Segmented G0–G5 storm-scale bar with the current level lit and glowing.

    Active segment gets a shadow glow; inactive segments are muted.
    """
    segments: list[ft.Control] = []
    for g in range(6):
        active = g == level
        color = (
            AppColors.SEVERITY_LOW
            if g == 0
            else AppColors.SEVERITY_MODERATE
            if g <= 2
            else AppColors.SEVERITY_CRITICAL
        )
        segments.append(
            ft.Container(
                content=ft.Text(
                    f"G{g}",
                    size=tokens.FONT_XXS,
                    weight=ft.FontWeight.W_700,
                    color=ft.Colors.WHITE if active else ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                ),
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding(4, 3, 4, 3),
                border_radius=tokens.RADIUS_XS,
                bgcolor=ft.Colors.with_opacity(0.9 if active else 0.08, color),
                border=ft.Border.all(
                    1,
                    ft.Colors.with_opacity(0.6 if active else 0.12, color),
                ),
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=8,
                    color=ft.Colors.with_opacity(0.5, color),
                )
                if active
                else None,
                expand=1,
            )
        )
    return ft.Row(segments, spacing=tokens.SPACE_XXS)


def build_kp_forecast_chips(forecast: list[dict]) -> ft.Control | None:
    """Row of next-24h predicted Kp chips ('HH:MM • Kp 3.0'), tinted by severity.

    The first chip (nearest future) gets a "now" marker dot.
    """
    if not forecast:
        return None
    chips = []
    for i, f in enumerate(forecast):
        try:
            kp = float(f.get("kp", 0.0))
        except (TypeError, ValueError):
            continue
        hour = str(f.get("time_tag", ""))[11:16] or "--:--"
        color = kp_severity_color(kp)
        is_now = i == 0
        chips.append(
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            hour,
                            size=tokens.FONT_XXS,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Text(
                            f"Kp {kp:.1f}",
                            size=tokens.FONT_XS,
                            weight=ft.FontWeight.W_700,
                            color=color,
                        ),
                        *(
                            [
                                ft.Container(
                                    width=6,
                                    height=6,
                                    border_radius=3,
                                    bgcolor=AppColors.PRIMARY,
                                )
                            ]
                            if is_now
                            else []
                        ),
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    tight=True,
                ),
                padding=ft.Padding(
                    tokens.SPACE_SM, tokens.SPACE_XS, tokens.SPACE_SM, tokens.SPACE_XS
                ),
                border_radius=tokens.RADIUS_SM,
                bgcolor=ft.Colors.with_opacity(0.1, color),
                border=ft.Border.all(1, ft.Colors.with_opacity(0.25, color)),
            )
        )
    return ft.Row(chips, spacing=tokens.SPACE_XS, scroll=ft.ScrollMode.AUTO)


@ft.component
def SpaceScreen() -> Control:
    state = ft.use_context(AppStateCtx)

    sw = state.space_weather or {}
    # Coerce at the boundary: feed can send "--"/None, and every consumer
    # below formats with :.1f or does numeric comparisons.
    from core.units import safe_float

    kp = safe_float(sw.get("kp_index"), 0.0) or 0.0
    status = sw.get("geomagnetic_status", "Quiet (Normal)")
    solar = sw.get("solar_activity", "Normal")
    flare_class = sw.get("flare_class", "")
    raw_kp = sw.get("raw_kp", [])
    # Sanitize at the boundary: chart code does float(v) + "{:.0f}".format(v)
    # and crashes on "--"/None sentinels from the feed.
    raw_flux = sw.get("xray_flux", [])
    xray_flux = (
        [v for v in raw_flux if isinstance(v, (int, float))]
        if isinstance(raw_flux, list)
        else []
    )
    kp_forecast = sw.get("kp_forecast", [])

    # Extract historical Kp values (handling both dict and list schemas from NOAA SWPC)
    kp_history: list[float] = []
    for item in raw_kp:
        if isinstance(item, dict):
            # NOAA products feed uses "Kp" (capital); other SWPC feeds use
            # lowercase variants — accept both so no reading is dropped.
            val = item.get(
                "Kp",
                item.get("kp", item.get("estimated_kp", item.get("kp_index"))),
            )
            if val is not None:
                try:
                    kp_history.append(float(val))
                except Exception as ex:
                    logger.debug("Suppressed exception: %s", ex)
        elif isinstance(item, list) and len(item) > 1:
            try:
                kp_history.append(float(item[1]))
            except Exception as ex:
                logger.debug("Suppressed exception: %s", ex)

    kp_color = (
        AppColors.SEVERITY_LOW
        if kp < 4.0
        else (AppColors.SEVERITY_MODERATE if kp < 6.0 else AppColors.SEVERITY_CRITICAL)
    )

    from flet import context as flet_context

    page = flet_context.page

    return ft.ListView(
        controls=[
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
                            # NOAA G-scale storm meter — the official severity scale
                            build_g_scale_meter(g_level_from_kp(kp)),
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
                            *(
                                [
                                    TelemetryLineChart(
                                        values=kp_history,
                                        accent_color=AppColors.ATMOSPHERE,
                                        height=140,
                                        step_direction=0.0,
                                        curved=False,
                                        left_axis_title="Kp",
                                    )
                                ]
                                if kp_history
                                else [
                                    ft.Container(
                                        content=ft.Text(
                                            "Awaiting telemetry stream…",
                                            size=tokens.FONT_XS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                        height=140,
                                        alignment=ft.Alignment.CENTER,
                                    )
                                ]
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
            # Solar X-ray flux — the live flare watch trace from GOES
            SectionHeader("SOLAR X-RAY FLUX (GOES 0.1–0.8NM)"),
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            ft.Text(
                                "6-hour X-ray irradiance trace — flares appear as spikes "
                                "(×10⁻⁹ W/m²; A/B < 100, C ~100–1k, M ~1k–10k, X > 10k)",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                font_family="Outfit",
                            ),
                            *(
                                [
                                    TelemetryLineChart(
                                        values=xray_flux,
                                        accent_color=AppColors.OCEAN,
                                        height=140,
                                        tooltip_format="{:.0f}",
                                    )
                                ]
                                if xray_flux
                                else [
                                    ft.Container(
                                        content=ft.Text(
                                            "Awaiting telemetry stream…",
                                            size=tokens.FONT_XS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                        height=140,
                                        alignment=ft.Alignment.CENTER,
                                    )
                                ]
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
            # Next 24h geomagnetic outlook (predicted Kp from NOAA SWPC)
            SectionHeader("NEXT 24H GEOMAGNETIC OUTLOOK"),
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Column(
                        [
                            ft.Text(
                                "Predicted planetary K-index (3-hour cadence, NOAA SWPC)",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                font_family="Outfit",
                            ),
                            *(
                                [build_kp_forecast_chips(kp_forecast)]
                                if kp_forecast
                                else [
                                    ft.Text(
                                        "No forecast available",
                                        size=tokens.FONT_XS,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    )
                                ]
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
                                            "Geomagnetic Storm",
                                            size=tokens.FONT_XS,
                                            weight=ft.FontWeight.W_500,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
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
                                padding=ft.Padding(
                                    tokens.SPACE_MD,
                                    tokens.SPACE_SM,
                                    tokens.SPACE_MD,
                                    tokens.SPACE_SM,
                                ),
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            "Solar Flare (GOES)",
                                            size=tokens.FONT_XS,
                                            weight=ft.FontWeight.W_500,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                        ft.Row(
                                            [
                                                ft.Text(
                                                    solar,
                                                    size=tokens.FONT_SM,
                                                    weight=ft.FontWeight.BOLD,
                                                    color=AppColors.PRIMARY,
                                                ),
                                                *(
                                                    [
                                                        ft.Container(
                                                            content=ft.Text(
                                                                flare_class,
                                                                size=tokens.FONT_XXS,
                                                                weight=ft.FontWeight.W_700,
                                                                color=ft.Colors.WHITE,
                                                            ),
                                                            bgcolor=AppColors.ERROR
                                                            if flare_class.startswith(
                                                                "X"
                                                            )
                                                            else AppColors.WARNING
                                                            if flare_class.startswith(
                                                                "M"
                                                            )
                                                            else AppColors.PRIMARY,
                                                            padding=ft.Padding(
                                                                6, 2, 6, 2
                                                            ),
                                                            border_radius=tokens.RADIUS_SM,
                                                        )
                                                    ]
                                                    if flare_class
                                                    else []
                                                ),
                                            ],
                                            spacing=tokens.SPACE_XS,
                                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                padding=ft.Padding(
                                    tokens.SPACE_MD,
                                    tokens.SPACE_SM,
                                    tokens.SPACE_MD,
                                    tokens.SPACE_SM,
                                ),
                            ),
                            ft.Divider(
                                height=1,
                                color=ft.Colors.with_opacity(0.1, ft.Colors.OUTLINE),
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Text(
                                            "Kp Index",
                                            size=tokens.FONT_XS,
                                            weight=ft.FontWeight.W_500,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                        ft.Text(
                                            f"{kp:.1f}",
                                            style=AppColors.data_text_style(
                                                size=tokens.FONT_MD, color=kp_color
                                            ),
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                padding=ft.Padding(
                                    tokens.SPACE_MD,
                                    tokens.SPACE_SM,
                                    tokens.SPACE_MD,
                                    tokens.SPACE_SM,
                                ),
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
            ft.Container(height=tokens.SPACE_MD),
            build_banner_ad(page),
            ft.Container(height=tokens.SPACE_XXXL),
        ],
        spacing=0,
        expand=True,
    )
