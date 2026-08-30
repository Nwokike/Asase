"""Settings About and Diagnostic Terminal section."""

import asyncio

import flet as ft

from components.activity_terminal import show_activity_terminal_dialog
from core import tokens
from core.constants import APP_NAME, APP_SUBTITLE, APP_VERSION
from core.state import state
from core.theme import AppColors, AppStyles, is_dark_mode


def build_terminal_card(page: ft.Page) -> ft.Container:
    """Builds the Live Activity Terminal Card."""
    return AppStyles.glass_card(
        ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(
                            ft.Icons.TERMINAL_ROUNDED,
                            size=tokens.ICON_MD,
                            color=AppColors.PRIMARY,
                        ),
                        width=tokens.ICON_BACKDROP,
                        height=tokens.ICON_BACKDROP,
                        border_radius=tokens.ICON_BACKDROP_RADIUS,
                        bgcolor=ft.Colors.with_opacity(
                            tokens.OPACITY_LIGHT, AppColors.PRIMARY
                        ),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "Live Activity Terminal",
                                size=tokens.FONT_MD,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(
                                "Stream real-time API logs, connection events, and raw telemetry.",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=tokens.SPACE_XXS,
                        expand=True,
                    ),
                    ft.FilledButton(
                        "Open Log",
                        icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                        style=ft.ButtonStyle(
                            bgcolor=AppColors.PRIMARY,
                            shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD),
                        ),
                        on_click=lambda _: show_activity_terminal_dialog(page),
                    ),
                ],
                spacing=tokens.SPACE_MD,
            ),
            padding=tokens.SPACE_MD,
        ),
        padding=0,
    )


def build_about_card(page: ft.Page) -> ft.Container:
    """Builds the About & Licenses Card with transparent adaptive vector icon."""
    is_dark = is_dark_mode(page)
    return AppStyles.glass_card(
        ft.Container(
            content=ft.Column(
                [
                    ft.Image(
                        src="/icon.svg",
                        width=56,
                        height=56,
                        color=ft.Colors.WHITE if is_dark else None,
                    ),
                    ft.Container(height=tokens.SPACE_XS),
                    ft.Text(
                        APP_NAME,
                        size=tokens.FONT_LG,
                        weight=ft.FontWeight.BOLD,
                        font_family="Outfit",
                    ),
                    ft.Text(
                        f"Version {APP_VERSION}",
                        size=tokens.FONT_SM,
                        color=AppColors.PRIMARY
                        if not is_dark
                        else AppColors.PRIMARY_LIGHT,
                        weight=ft.FontWeight.W_600,
                    ),
                    ft.Container(height=tokens.SPACE_XS),
                    ft.Text(
                        APP_SUBTITLE,
                        size=tokens.FONT_SM,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "Powered by Open-Meteo, USGS, NASA EONET & NOAA SWPC.\n100% Free & Open Public Domain Planetary Telemetry.",
                        size=tokens.FONT_XS,
                        color=ft.Colors.with_opacity(
                            tokens.OPACITY_DIM, ft.Colors.ON_SURFACE
                        ),
                        text_align=ft.TextAlign.CENTER,
                    ),
                    *(
                        [
                            ft.Container(height=tokens.SPACE_XS),
                            ft.TextButton(
                                "Ad Privacy Preferences (GDPR)",
                                icon=ft.Icons.PRIVACY_TIP_OUTLINED,
                                on_click=lambda _: (
                                    asyncio.create_task(
                                        state.ad_service.show_privacy_options()
                                    )
                                    if getattr(state, "ad_service", None)
                                    else None
                                ),
                            ),
                        ]
                        if getattr(state, "ad_service", None)
                        and state.ad_service.is_mobile()
                        else []
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=tokens.SPACE_XXS,
            ),
            padding=tokens.SPACE_LG,
            alignment=ft.Alignment.CENTER,
        ),
        padding=0,
    )
