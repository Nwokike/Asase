"""Offline banner — DDGS pattern."""

from __future__ import annotations

import flet as ft

from core import tokens
from core.theme import AppColors


def build_offline_banner(visible: bool) -> ft.Control:
    return ft.Container(
        visible=visible,
        content=ft.Row(
            [
                ft.Icon(
                    ft.Icons.WIFI_OFF_ROUNDED,
                    size=tokens.ICON_SM,
                    color=AppColors.ERROR,
                ),
                ft.Text(
                    "You’re offline — showing cached data",
                    size=tokens.FONT_XS,
                    color=AppColors.ERROR,
                    weight=ft.FontWeight.W_600,
                ),
            ],
            spacing=tokens.SPACE_XS,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.with_opacity(0.12, AppColors.ERROR),
        padding=ft.Padding(
            tokens.SPACE_MD, tokens.SPACE_SM, tokens.SPACE_MD, tokens.SPACE_SM
        ),
        border_radius=tokens.RADIUS_MD,
        margin=ft.Margin(tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0),
    )
