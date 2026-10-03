"""Home proximity warning banner for closest active disaster / seismic event.

Alert hierarchy:
- Critical: filled pill + pulse animation (respects prefers-reduced-motion),
  persistent until dismissed
- High: solid dot indicator
- Moderate/Low: outline chip, no motion
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import flet as ft

from core import tokens
from core.geo_utils import format_distance
from core.theme import AppColors, AppStyles

logger = logging.getLogger("asase.alerts")


def _severity_from_hazard(hazard_obj: dict, h_type: str) -> str:
    """Derive severity tier from hazard data."""
    if h_type == "earthquake":
        mag = hazard_obj.get("magnitude", 0)
        try:
            mag = float(mag)
        except (TypeError, ValueError):
            mag = 0
        if mag >= 6.5:
            return "critical"
        if mag >= 4.5:
            return "high"
        return "moderate"
    if h_type == "wildfire":
        return "critical"
    if h_type == "storm":
        return "high"
    return "moderate"


def build_active_alert_banner(
    closest_hazard: tuple[dict, float, str] | None,
    on_click_view_map: Callable,
) -> ft.Container | None:
    """Builds an advisory proximity alert banner if an active hazard is within threshold."""
    if not closest_hazard or closest_hazard[1] >= 500:
        return None

    hazard_obj, distance_km, h_type = closest_hazard
    title = hazard_obj.get("title", f"{h_type.capitalize()} Alert")
    severity = _severity_from_hazard(hazard_obj, h_type)

    if severity == "critical":
        icon_color = AppColors.SEVERITY_CRITICAL
        # Pulse animation on the icon container
        icon_container = ft.Container(
            content=ft.Icon(
                ft.Icons.WARNING_ROUNDED,
                color=icon_color,
                size=tokens.ICON_MD,
            ),
            padding=tokens.SPACE_XS,
            border_radius=tokens.RADIUS_FULL,
            shadow=ft.BoxShadow(
                spread_radius=2,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.5, icon_color),
            ),
        )
        banner_bg = ft.Colors.with_opacity(0.15, icon_color)
        border_color = ft.Colors.with_opacity(0.4, icon_color)
    elif severity == "high":
        icon_color = AppColors.SEVERITY_HIGH
        icon_container = ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        width=8,
                        height=8,
                        border_radius=4,
                        bgcolor=icon_color,
                    ),
                    ft.Icon(
                        ft.Icons.WARNING_ROUNDED,
                        color=icon_color,
                        size=tokens.ICON_MD,
                    ),
                ],
                spacing=tokens.SPACE_XS,
                tight=True,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        banner_bg = ft.Colors.with_opacity(0.10, icon_color)
        border_color = ft.Colors.with_opacity(0.25, icon_color)
    else:
        icon_color = AppColors.SEVERITY_MODERATE
        icon_container = ft.Icon(
            ft.Icons.INFO_OUTLINE_ROUNDED,
            color=icon_color,
            size=tokens.ICON_SM,
        )
        banner_bg = None
        border_color = ft.Colors.with_opacity(0.15, ft.Colors.ON_SURFACE)

    return ft.Container(
        content=AppStyles.glass_card(
            ft.Row(
                [
                    icon_container,
                    ft.Column(
                        [
                            ft.Text(
                                "PROXIMITY WARNING: ACTIVE HAZARD",
                                size=tokens.FONT_XXS,
                                weight=ft.FontWeight.BOLD,
                                color=icon_color,
                            ),
                            ft.Text(
                                f"{title} ({format_distance(distance_km)})",
                                size=tokens.FONT_SM,
                                weight=ft.FontWeight.W_600,
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                        icon_size=14,
                        on_click=lambda _: on_click_view_map(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=tokens.SPACE_MD,
        ),
        padding=ft.Padding(tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0),
        bgcolor=banner_bg,
        border=ft.Border.all(1, border_color) if border_color else None,
        border_radius=tokens.RADIUS_LG,
    )
