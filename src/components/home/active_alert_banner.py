"""Home proximity warning banner for closest active disaster / seismic event."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from core import tokens
from core.geo_utils import format_distance
from core.theme import AppColors, AppStyles


def build_active_alert_banner(
    closest_hazard: tuple[dict, float, str] | None,
    on_click_view_map: Callable,
) -> ft.Container | None:
    """Builds an advisory proximity alert banner if an active hazard is within threshold."""
    if not closest_hazard or closest_hazard[1] >= 500:
        return None

    hazard_obj, distance_km, h_type = closest_hazard
    title = hazard_obj.get("title", f"{h_type.capitalize()} Alert")

    return ft.Container(
        content=AppStyles.glass_card(
            ft.Row(
                [
                    ft.Icon(
                        ft.Icons.WARNING_ROUNDED,
                        color=AppColors.SEVERITY_HIGH,
                        size=tokens.ICON_MD,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "PROXIMITY WARNING: ACTIVE HAZARD",
                                size=tokens.FONT_XXS,
                                weight=ft.FontWeight.BOLD,
                                color=AppColors.SEVERITY_HIGH,
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
    )
