"""Telemetry metric and hazard cards with responsive styling."""

from __future__ import annotations

import flet as ft

from core import tokens
from core.theme import (
    AppColors,
    AppStyles,
)


def build_severity_badge(severity: str, label: str) -> ft.Container:
    """Build a pulsating color badge for risk severity."""
    color_map = {
        "low": AppColors.SEVERITY_LOW,
        "moderate": AppColors.SEVERITY_MODERATE,
        "high": AppColors.SEVERITY_HIGH,
        "critical": AppColors.SEVERITY_CRITICAL,
    }
    color = color_map.get(severity.lower(), AppColors.GREY)
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    width=6,
                    height=6,
                    border_radius=3,
                    bgcolor=color,
                ),
                ft.Text(
                    label.upper(),
                    size=tokens.FONT_XXS,
                    weight=ft.FontWeight.W_700,
                    color=color,
                    font_family="Outfit",
                ),
            ],
            spacing=4,
            tight=True,
        ),
        padding=ft.Padding(8, 4, 8, 4),
        border_radius=tokens.RADIUS_FULL,
        bgcolor=ft.Colors.with_opacity(0.12, color),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.3, color)),
    )


def TelemetryCard(
    icon: ft.IconData,
    title: str,
    value: str,
    subtitle: str,
    severity: str = "low",
    accent_color: str = AppColors.PRIMARY,
    on_click=None,
) -> ft.Container:
    """A responsive telemetry metric card."""
    content = ft.Column(
        [
            ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=tokens.ICON_SM, color=accent_color),
                        width=32,
                        height=32,
                        border_radius=8,
                        bgcolor=ft.Colors.with_opacity(0.12, accent_color),
                        alignment=ft.Alignment.CENTER,
                    ),
                    build_severity_badge(severity, severity),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Container(height=tokens.SPACE_XS),
            ft.Text(
                value,
                size=tokens.FONT_XL,
                weight=ft.FontWeight.BOLD,
                font_family="Outfit",
            ),
            ft.Text(
                title,
                size=tokens.FONT_SM,
                weight=ft.FontWeight.W_600,
                color=ft.Colors.ON_SURFACE,
                font_family="Outfit",
            ),
            ft.Text(
                subtitle,
                size=tokens.FONT_XS,
                color=ft.Colors.ON_SURFACE_VARIANT,
                font_family="Outfit",
                max_lines=2,
                overflow=ft.TextOverflow.ELLIPSIS,
            ),
        ],
        spacing=2,
        tight=True,
    )

    return AppStyles.glass_card(content, padding=tokens.SPACE_MD, on_click=on_click)
