"""OnboardingScreen — modern hero welcome & planetary defense feature showcase."""

from __future__ import annotations

import flet as ft
from flet import Control

from core import tokens
from core.constants import STORAGE_ONBOARDING_DONE
from core.theme import AppColors, AppStyles, build_logo, is_dark_mode
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

# Feature showcase cards: (icon, title, description, accent color)
_FEATURES = [
    (
        ft.Icons.CRISIS_ALERT_ROUNDED,
        "Live Seismic Network",
        "USGS global earthquake telemetry with real-time magnitude alerts",
        AppColors.SEVERITY_CRITICAL,
    ),
    (
        ft.Icons.LOCAL_FIRE_DEPARTMENT_ROUNDED,
        "Multi-Hazard Watch",
        "NASA EONET wildfires, storms, floods & active volcanic events",
        AppColors.WARNING,
    ),
    (
        ft.Icons.TSUNAMI_ROUNDED,
        "Hydrology & Atmosphere",
        "Open-Meteo GloFAS river discharge, flood peaks & global AQI",
        AppColors.OCEAN,
    ),
    (
        ft.Icons.PSYCHOLOGY_ROUNDED,
        "Grounded AI Intelligence",
        "Multi-hazard risk dossiers synthesized from live telemetry",
        AppColors.ATMOSPHERE,
    ),
]


def _feature_card(icon, title: str, description: str, accent: str, is_dark: bool):
    return AppStyles.glass_card(
        ft.Container(
            content=ft.Row(
                [
                    ft.Container(
                        content=ft.Icon(icon, size=tokens.ICON_MD, color=accent),
                        width=46,
                        height=46,
                        border_radius=23,
                        bgcolor=ft.Colors.with_opacity(0.12, accent),
                        alignment=ft.Alignment.CENTER,
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                title,
                                size=tokens.FONT_SM,
                                weight=ft.FontWeight.W_600,
                                font_family="Outfit",
                                max_lines=1,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                            ft.Text(
                                description,
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=tokens.SPACE_XXS,
                        expand=True,
                    ),
                ],
                spacing=tokens.SPACE_MD,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=tokens.SPACE_MD,
        ),
        padding=0,
    )


def _build_feature_grid(page: ft.Page | None):
    is_dark = is_dark_mode(page)
    return ft.Column(
        [
            _feature_card(icon, title, desc, accent, is_dark)
            for icon, title, desc, accent in _FEATURES
        ],
        spacing=tokens.SPACE_SM,
    )


def build_onboarding_view(on_accept=None, page: ft.Page | None = None) -> Control:
    """Builds the modern onboarding hero layout with the theme-reactive logo and no duplicate text."""
    hero = ft.Container(
        content=ft.Column(
            [
                build_logo(page, height=72),
                ft.Container(height=tokens.SPACE_MD),
                ft.Text(
                    "Real-time planetary telemetry & multi-hazard intelligence fused into a single unified command interface.",
                    size=tokens.FONT_SM,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=3,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
        padding=ft.Padding(
            tokens.SPACE_LG, tokens.SPACE_MD, tokens.SPACE_LG, tokens.SPACE_SM
        ),
        alignment=ft.Alignment.CENTER,
    )

    content_box = ft.Container(
        content=ft.Column(
            [
                hero,
                ft.Container(height=tokens.SPACE_XS),
                _build_feature_grid(page),
                ft.Container(height=tokens.SPACE_LG),
                ft.Column(
                    [
                        ft.FilledButton(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.ROCKET_LAUNCH_ROUNDED,
                                        size=tokens.ICON_SM,
                                        color=ft.Colors.WHITE,
                                    ),
                                    ft.Text(
                                        "Enter Planetary Command",
                                        size=tokens.FONT_MD,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.WHITE,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=tokens.SPACE_SM,
                            ),
                            style=ft.ButtonStyle(
                                bgcolor=AppColors.PRIMARY,
                                padding=tokens.SPACE_LG,
                                shape=ft.RoundedRectangleBorder(
                                    radius=tokens.RADIUS_LG
                                ),
                            ),
                            width=340,
                            height=52,
                            on_click=on_accept,
                        ),
                        ft.Container(height=tokens.SPACE_XXS),
                        ft.Text(
                            "100% free & open public-domain telemetry. No account required.",
                            size=tokens.FONT_XXS,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=tokens.SPACE_XS,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        ),
        width=540,
        alignment=ft.Alignment.CENTER,
    )

    return ft.Container(
        content=ft.ListView(
            controls=[
                ft.Container(
                    content=content_box,
                    alignment=ft.Alignment.CENTER,
                    padding=ft.Padding(
                        tokens.SPACE_MD,
                        tokens.SPACE_LG,
                        tokens.SPACE_MD,
                        tokens.SPACE_XL,
                    ),
                ),
            ],
            spacing=0,
            expand=True,
        ),
        expand=True,
    )


@ft.component
def OnboardingScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    from flet import context as flet_context

    page = flet_context.page

    async def _accept(e=None):
        state.has_accepted_terms = True
        state.is_first_launch = False
        state.telemetry_version += 1
        if controller.dismiss_onboarding:
            controller.dismiss_onboarding()
        if controller.save_setting:
            await controller.save_setting(STORAGE_ONBOARDING_DONE, "true")
        if page:
            page.update()

    return build_onboarding_view(_accept, page)
