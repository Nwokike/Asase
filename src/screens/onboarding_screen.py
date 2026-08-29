"""OnboardingScreen — Welcome & Planetary Defense Terms."""

from __future__ import annotations

import asyncio

import flet as ft
from flet import Control

from core import tokens
from core.constants import APP_NAME, APP_SUBTITLE, STORAGE_ONBOARDING_DONE
from core.theme import AppColors
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx


@ft.component
def OnboardingScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    async def _accept():
        state.has_accepted_terms = True
        state.is_first_launch = False
        if controller.save_setting:
            await controller.save_setting(STORAGE_ONBOARDING_DONE, "true")

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(expand=True),
                ft.Image(src="icon.png", width=96, height=96),
                ft.Container(height=tokens.SPACE_MD),
                ft.Text(
                    APP_NAME,
                    size=tokens.FONT_HERO,
                    weight=ft.FontWeight.BOLD,
                    font_family="Outfit",
                ),
                ft.Text(
                    APP_SUBTITLE,
                    size=tokens.FONT_MD,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=tokens.SPACE_XL),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE_ROUNDED,
                                        color=AppColors.PRIMARY,
                                        size=tokens.ICON_SM,
                                    ),
                                    ft.Text(
                                        "Live USGS Global Earthquake Feeds",
                                        size=tokens.FONT_SM,
                                    ),
                                ],
                                spacing=tokens.SPACE_SM,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE_ROUNDED,
                                        color=AppColors.PRIMARY,
                                        size=tokens.ICON_SM,
                                    ),
                                    ft.Text(
                                        "NASA EONET Wildfires & Storms",
                                        size=tokens.FONT_SM,
                                    ),
                                ],
                                spacing=tokens.SPACE_SM,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE_ROUNDED,
                                        color=AppColors.PRIMARY,
                                        size=tokens.ICON_SM,
                                    ),
                                    ft.Text(
                                        "Open-Meteo GloFAS River Flood Forecasting",
                                        size=tokens.FONT_SM,
                                    ),
                                ],
                                spacing=tokens.SPACE_SM,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE_ROUNDED,
                                        color=AppColors.PRIMARY,
                                        size=tokens.ICON_SM,
                                    ),
                                    ft.Text(
                                        "Real-time Global Air Quality Index (AQI)",
                                        size=tokens.FONT_SM,
                                    ),
                                ],
                                spacing=tokens.SPACE_SM,
                            ),
                            ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.CHECK_CIRCLE_ROUNDED,
                                        color=AppColors.PRIMARY,
                                        size=tokens.ICON_SM,
                                    ),
                                    ft.Text(
                                        "NOAA Space Weather & Kp-Index Telemetry",
                                        size=tokens.FONT_SM,
                                    ),
                                ],
                                spacing=tokens.SPACE_SM,
                            ),
                        ],
                        spacing=tokens.SPACE_SM,
                    ),
                    padding=tokens.SPACE_LG,
                    border_radius=tokens.RADIUS_LG,
                    bgcolor=ft.Colors.with_opacity(0.08, AppColors.PRIMARY),
                    border=ft.Border.all(
                        1, ft.Colors.with_opacity(0.2, AppColors.PRIMARY)
                    ),
                ),
                ft.Container(expand=True),
                ft.FilledButton(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Enter Planetary Command",
                                size=tokens.FONT_MD,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    style=ft.ButtonStyle(
                        bgcolor=AppColors.PRIMARY,
                        padding=tokens.SPACE_MD,
                        shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD),
                    ),
                    width=320,
                    on_click=lambda _: asyncio.create_task(_accept()),
                ),
                ft.Container(height=tokens.SPACE_XL),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
        padding=tokens.SPACE_XL,
        alignment=ft.Alignment.CENTER,
        expand=True,
    )
