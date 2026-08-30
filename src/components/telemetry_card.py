"""Reusable TelemetryCard with Glassmorphism, Severity Indicators, Distance, and Actions."""

from __future__ import annotations

import asyncio

import flet as ft

from core import tokens
from core.geo_utils import calculate_haversine_distance_km, format_distance
from core.theme import AppColors, AppStyles
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx


def build_severity_badge(severity: str, label: str = "") -> ft.Container:
    """Returns a styled Container badge for severity display."""
    if severity == "critical":
        badge_color = AppColors.SEVERITY_CRITICAL
        text = label.upper() if label else "CRITICAL"
    elif severity == "high":
        badge_color = AppColors.SEVERITY_HIGH
        text = label.upper() if label else "ELEVATED"
    elif severity == "moderate":
        badge_color = AppColors.SEVERITY_MODERATE
        text = label.upper() if label else "MODERATE"
    else:
        badge_color = AppColors.SEVERITY_LOW
        text = label.upper() if label else "NOMINAL"

    return ft.Container(
        content=ft.Text(
            text,
            size=tokens.FONT_XXS,
            weight=ft.FontWeight.W_700,
            color=badge_color,
            font_family="Outfit",
        ),
        padding=ft.Padding(6, 2, 6, 2),
        border_radius=tokens.RADIUS_SM,
        bgcolor=ft.Colors.with_opacity(0.12, badge_color),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.25, badge_color)),
    )


def TelemetryCard(
    title: str,
    subtitle: str,
    value: str,
    severity: str = "low",
    icon: ft.IconData = ft.Icons.INFO_OUTLINE_ROUNDED,
    accent_color: str | None = None,
    event_lat: float | None = None,
    event_lon: float | None = None,
    event_url: str = "",
    on_click=None,
) -> ft.Control:
    """Builds a responsive telemetry card with distance calculation and share/link buttons."""

    if severity == "critical":
        badge_color = AppColors.SEVERITY_CRITICAL
        badge_text = "CRITICAL"
    elif severity == "high":
        badge_color = AppColors.SEVERITY_HIGH
        badge_text = "ELEVATED"
    elif severity == "moderate":
        badge_color = AppColors.SEVERITY_MODERATE
        badge_text = "MODERATE"
    else:
        badge_color = AppColors.SEVERITY_LOW
        badge_text = "NOMINAL"

    final_accent = accent_color or badge_color

    @ft.component
    def _CardBody():
        state = ft.use_context(AppStateCtx)
        controller = ft.use_context(ControllerMethodsCtx)

        dist_str = ""
        if event_lat is not None and event_lon is not None:
            dist_km = calculate_haversine_distance_km(
                state.current_lat, state.current_lon, event_lat, event_lon
            )
            dist_str = format_distance(dist_km)

        def _on_share_click(e):
            if controller.share_text:
                msg = (
                    f"\U0001f30d ASASE PLANETARY ALERT:\n{title}\n{subtitle}"
                    f"\nSeverity: {badge_text}\nLocation: {dist_str if dist_str else 'Global'}\n{event_url}"
                )
                asyncio.create_task(controller.share_text(msg, title))

        def _on_link_click(e):
            if controller.launch_url and event_url:
                asyncio.create_task(controller.launch_url(event_url))

        return AppStyles.glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Row(
                                [
                                    ft.Container(
                                        content=ft.Icon(
                                            icon,
                                            size=tokens.ICON_SM,
                                            color=final_accent,
                                        ),
                                        padding=tokens.SPACE_XS,
                                        border_radius=tokens.RADIUS_SM,
                                        bgcolor=ft.Colors.with_opacity(
                                            0.12, final_accent
                                        ),
                                    ),
                                    ft.Text(
                                        badge_text,
                                        size=tokens.FONT_XXS,
                                        weight=ft.FontWeight.W_700,
                                        color=final_accent,
                                        font_family="Outfit",
                                    ),
                                ],
                                spacing=tokens.SPACE_XS,
                            ),
                            ft.Row(
                                [
                                    *(
                                        [
                                            ft.IconButton(
                                                icon=ft.Icons.SHARE_ROUNDED,
                                                icon_size=16,
                                                tooltip="Share Alert",
                                                on_click=_on_share_click,
                                            )
                                        ]
                                        if controller.share_text
                                        else []
                                    ),
                                    *(
                                        [
                                            ft.IconButton(
                                                icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                                                icon_size=16,
                                                tooltip="Official Source",
                                                on_click=_on_link_click,
                                            )
                                        ]
                                        if event_url and controller.launch_url
                                        else []
                                    ),
                                ],
                                spacing=0,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        title,
                        size=tokens.FONT_MD,
                        weight=ft.FontWeight.BOLD,
                        max_lines=2,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        font_family="Outfit",
                    ),
                    ft.Row(
                        [
                            ft.Text(
                                subtitle,
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                expand=True,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            *(
                                [
                                    ft.Container(
                                        content=ft.Row(
                                            [
                                                ft.Icon(
                                                    ft.Icons.NEAR_ME_ROUNDED,
                                                    size=12,
                                                    color=AppColors.PRIMARY,
                                                ),
                                                ft.Text(
                                                    dist_str,
                                                    size=tokens.FONT_XXS,
                                                    weight=ft.FontWeight.W_600,
                                                    color=AppColors.PRIMARY,
                                                ),
                                            ],
                                            spacing=2,
                                            tight=True,
                                        ),
                                        padding=ft.Padding(6, 2, 6, 2),
                                        border_radius=tokens.RADIUS_SM,
                                        bgcolor=ft.Colors.with_opacity(
                                            0.1, AppColors.PRIMARY
                                        ),
                                    )
                                ]
                                if dist_str
                                else []
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    *(
                        [
                            ft.Text(
                                value,
                                size=tokens.FONT_SM,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE,
                            )
                        ]
                        if value
                        else []
                    ),
                ],
                spacing=tokens.SPACE_XS,
            ),
            padding=tokens.SPACE_MD,
            on_click=on_click,
        )

    try:
        return _CardBody()
    except RuntimeError:
        # Fallback for unit tests without a Renderer (no React context)
        return AppStyles.glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(
                                    icon, size=tokens.ICON_SM, color=final_accent
                                ),
                                padding=tokens.SPACE_XS,
                                border_radius=tokens.RADIUS_SM,
                                bgcolor=ft.Colors.with_opacity(0.12, final_accent),
                            ),
                            ft.Text(
                                badge_text,
                                size=tokens.FONT_XXS,
                                weight=ft.FontWeight.W_700,
                                color=final_accent,
                                font_family="Outfit",
                            ),
                        ],
                        spacing=tokens.SPACE_XS,
                    ),
                    ft.Text(
                        title,
                        size=tokens.FONT_MD,
                        weight=ft.FontWeight.BOLD,
                        font_family="Outfit",
                    ),
                    ft.Text(
                        subtitle,
                        size=tokens.FONT_XS,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    *(
                        [
                            ft.Text(
                                value,
                                size=tokens.FONT_SM,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.ON_SURFACE,
                            )
                        ]
                        if value
                        else []
                    ),
                ],
                spacing=tokens.SPACE_XS,
            ),
            padding=tokens.SPACE_MD,
            on_click=on_click,
        )
