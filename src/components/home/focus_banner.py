"""Focus banner — auto-expanding "Now Tracking" summary card for the Home screen.

Two states:
- Collapsed: the compact tracking pill (tap to expand).
- Expanded: a glass summary card with location header, quick stat chips
  (elevation / temperature / AQI / Kp / nearest hazard) and a prominent
  "Open Full Dossier" button — the obvious entry point the pill wasn't.

Auto-opens right after a search or bookmark selection; collapses back to
the pill via the chevron. All data comes from observable AppState fields,
so the chips fill in live as the post-search telemetry refresh lands.
"""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors, AppStyles


def _fmt_num(value: object, pattern: str) -> str:
    """Format a telemetry value, degrading to 'n/a' for missing/odd data."""
    try:
        if value is None or value == "":
            return "n/a"
        return pattern.format(float(value))
    except (TypeError, ValueError):
        return "n/a"


def _stat_chip(
    page: ft.Page | None, icon: ft.IconData, label: str, color: str
) -> ft.Container:
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icon, size=tokens.ICON_XS, color=color),
                ft.Text(
                    label,
                    size=tokens.FONT_XS,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.ON_SURFACE,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
            ],
            spacing=tokens.SPACE_XXS,
            tight=True,
        ),
        padding=ft.Padding(
            tokens.SPACE_SM, tokens.SPACE_XS, tokens.SPACE_SM, tokens.SPACE_XS
        ),
        border_radius=tokens.RADIUS_FULL,
        bgcolor=ft.Colors.with_opacity(tokens.OPACITY_SUBTLE, color),
        border=ft.Border.all(1, ft.Colors.with_opacity(tokens.OPACITY_LIGHT, color)),
    )


def build_focus_banner(
    page: ft.Page | None,
    location_name: str,
    country: str,
    elevation_m: float,
    temperature: object,
    us_aqi: object,
    kp_index: object,
    nearest_hazard_text: str | None,
    nearest_hazard_color: str,
    expanded: bool,
    is_loading: bool,
    on_toggle: Callable,
    on_open_dossier: Callable,
) -> ft.Control:
    """Builds the two-state Now-Tracking banner (pill collapsed / card expanded)."""
    name = location_name or "Global Telemetry"
    header = f"{name}{f', {country}' if country else ''}"

    if not expanded:
        pill = ft.Container(
            content=ft.Row(
                [
                    ft.Icon(
                        ft.Icons.LOCATION_ON_ROUNDED,
                        size=tokens.ICON_XS,
                        color=AppColors.PRIMARY,
                    ),
                    ft.Text(
                        f"Tracking: {name}",
                        size=tokens.FONT_XS,
                        weight=ft.FontWeight.W_600,
                        color=AppColors.PRIMARY,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Icon(
                        ft.Icons.EXPAND_MORE_ROUNDED,
                        size=tokens.ICON_XS,
                        color=AppColors.PRIMARY,
                    ),
                ],
                spacing=tokens.SPACE_XXS,
                tight=True,
            ),
            padding=ft.Padding(
                tokens.SPACE_MD, tokens.SPACE_XS, tokens.SPACE_MD, tokens.SPACE_XS
            ),
            border_radius=tokens.RADIUS_FULL,
            bgcolor=ft.Colors.with_opacity(0.1, AppColors.PRIMARY),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.3, AppColors.PRIMARY)),
            on_click=lambda _: on_toggle(),
            ink=True,
        )
        return ft.Container(
            content=ft.Row([pill], alignment=ft.MainAxisAlignment.CENTER),
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding(tokens.SPACE_LG, tokens.SPACE_XS, tokens.SPACE_LG, 0),
        )

    temp_str = _fmt_num(temperature, "{:.0f}°C")
    aqi_str = _fmt_num(us_aqi, "AQI {:.0f}")
    kp_str = _fmt_num(kp_index, "Kp {:.1f}")
    elev_str = _fmt_num(elevation_m, "{:,.0f} m")

    chips_row = ft.Row(
        [
            _stat_chip(page, ft.Icons.TERRAIN_ROUNDED, elev_str, AppColors.PRIMARY),
            _stat_chip(page, ft.Icons.THERMOSTAT_ROUNDED, temp_str, AppColors.OCEAN),
            _stat_chip(page, ft.Icons.AIR_ROUNDED, aqi_str, AppColors.INFO),
            _stat_chip(page, ft.Icons.PUBLIC_ROUNDED, kp_str, AppColors.ATMOSPHERE),
        ],
        spacing=tokens.SPACE_XS,
        wrap=True,
        run_spacing=tokens.SPACE_XS,
    )

    hazard_row = None
    if nearest_hazard_text:
        hazard_row = _stat_chip(
            page, ft.Icons.WARNING_ROUNDED, nearest_hazard_text, nearest_hazard_color
        )

    loading_row = (
        ft.Row(
            [
                ft.ProgressRing(width=14, height=14, stroke_width=2),
                ft.Text(
                    "Updating live telemetry for this location...",
                    size=tokens.FONT_XS,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=tokens.SPACE_XS,
            tight=True,
        )
        if is_loading
        else None
    )

    column = ft.Column(
        [
            ft.Row(
                [
                    ft.Icon(
                        ft.Icons.LOCATION_ON_ROUNDED,
                        size=tokens.ICON_MD,
                        color=AppColors.PRIMARY,
                    ),
                    ft.Text(
                        header,
                        size=tokens.FONT_MD,
                        weight=ft.FontWeight.W_700,
                        font_family="Outfit",
                        color=ft.Colors.ON_SURFACE,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.IconButton(
                        icon=(
                            ft.Icons.EXPAND_LESS_ROUNDED
                            if expanded
                            else ft.Icons.EXPAND_MORE_ROUNDED
                        ),
                        icon_size=tokens.ICON_SM,
                        icon_color=AppColors.PRIMARY,
                        tooltip="Collapse",
                        on_click=lambda _: on_toggle(),
                    ),
                ],
                spacing=tokens.SPACE_XS,
            ),
            chips_row,
            *([hazard_row] if hazard_row else []),
            *([ft.Container(height=tokens.SPACE_XS)] if loading_row else []),
            *([loading_row] if loading_row else []),
            ft.Container(height=tokens.SPACE_XS),
            ft.Row(
                [
                    ft.FilledButton(
                        icon=ft.Icons.ANALYTICS_ROUNDED,
                        content=ft.Text(
                            "OPEN FULL DOSSIER",
                            size=tokens.FONT_SM,
                            weight=ft.FontWeight.W_700,
                            color=ft.Colors.WHITE,
                        ),
                        style=ft.ButtonStyle(
                            bgcolor=AppColors.PRIMARY,
                            shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD),
                        ),
                        on_click=lambda _: on_open_dossier(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        spacing=tokens.SPACE_XS,
        tight=True,
    )

    return ft.Container(
        content=AppStyles.glass_card(column, page=page, padding=tokens.SPACE_MD),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding(
            tokens.SPACE_LG, tokens.SPACE_XS, tokens.SPACE_LG, tokens.SPACE_XS
        ),
    )


__all__ = ["build_focus_banner"]
