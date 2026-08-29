"""Animated Shimmer Skeleton Loader for telemetry cards and charts."""

from __future__ import annotations

import flet as ft

from core import tokens
from core.theme import AppColors


def TelemetrySkeletonCard(height: float = 110) -> ft.Control:
    """Builds an animated shimmer placeholder card."""
    skeleton_box = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            width=80,
                            height=16,
                            border_radius=tokens.RADIUS_SM,
                            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        ),
                        ft.Container(
                            width=50,
                            height=16,
                            border_radius=tokens.RADIUS_SM,
                            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    width=200,
                    height=20,
                    border_radius=tokens.RADIUS_SM,
                    bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
                ),
                ft.Container(
                    width=140,
                    height=14,
                    border_radius=tokens.RADIUS_SM,
                    bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                ),
            ],
            spacing=tokens.SPACE_SM,
        ),
        padding=tokens.SPACE_MD,
        border_radius=tokens.RADIUS_LG,
        bgcolor=ft.Colors.with_opacity(0.06, AppColors.DARK_SURFACE),
        border=ft.Border.all(1, ft.Colors.with_opacity(0.08, ft.Colors.WHITE)),
        height=height,
    )

    return ft.Shimmer(
        content=skeleton_box,
        base_color=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
        highlight_color=ft.Colors.with_opacity(0.18, ft.Colors.WHITE),
        period=1200,
    )
