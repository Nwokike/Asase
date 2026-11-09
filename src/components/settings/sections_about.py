"""Settings About and Diagnostic Terminal section."""

import flet as ft

from components.activity_terminal import show_activity_terminal_dialog
from core import tokens
from core.constants import (
    APP_VERSION,
    CONTACT_EMAIL,
    GITHUB_REPO_URL,
    KIRI_APPS_PLAY_URL,
    KIRI_APPS_URL,
)
from core.state import state
from core.tasks import schedule
from core.theme import AppColors, AppStyles, build_logo, is_dark_mode


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


def _is_store_device(page: ft.Page | None) -> bool:
    """Phones/TV are the Play audience; desktop/web star on GitHub (KTV)."""
    try:
        return page is not None and page.platform in (
            ft.PagePlatform.ANDROID,
            ft.PagePlatform.IOS,
            ft.PagePlatform.ANDROID_TV,
        )
    except Exception:
        return False


def build_about_card(
    page: ft.Page,
    launch_url=None,  # controller.launch_url — async (url)
) -> ft.Container:
    """Builds the About & Licenses Card with theme-reactive full logo.

    Family pattern (ktv-player / DDGS): tappable icon rows for Contact,
    Rate and More apps from Kiri — the Play developer listing on store
    devices, the kiri.ng showcase everywhere else.
    """
    is_dark = is_dark_mode(page)

    def _open_version_dialog(e=None):
        from components.version_dialog import show_version_dialog

        show_version_dialog(page)

    def _open(url: str):
        if launch_url:
            schedule(launch_url, url, page=page)

    def _row(icon, title: str, subtitle: str, url: str):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icon, size=tokens.ICON_MD, color=AppColors.PRIMARY),
                    ft.Column(
                        [
                            ft.Text(
                                title,
                                size=tokens.FONT_SM,
                                weight=ft.FontWeight.W_600,
                            ),
                            ft.Text(
                                subtitle,
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=tokens.SPACE_XXS,
                        expand=True,
                    ),
                    ft.Icon(
                        ft.Icons.OPEN_IN_NEW_ROUNDED,
                        size=15,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                ],
                spacing=tokens.SPACE_MD,
            ),
            ink=True,
            border_radius=tokens.RADIUS_MD,
            on_click=lambda _, _url=url: _open(_url),
        )

    store = _is_store_device(page)

    return AppStyles.glass_card(
        ft.Container(
            content=ft.Column(
                [
                    build_logo(page, height=54, width=180),
                    ft.Container(height=tokens.SPACE_XXS),
                    ft.Container(
                        content=ft.Text(
                            f"Version {APP_VERSION}",
                            size=tokens.FONT_SM,
                            color=AppColors.PRIMARY
                            if not is_dark
                            else AppColors.PRIMARY_LIGHT,
                            weight=ft.FontWeight.W_600,
                        ),
                        ink=True,
                        tooltip="Tap to view changelog",
                        on_click=_open_version_dialog,
                    ),
                    ft.Container(height=tokens.SPACE_XS),
                    _row(
                        ft.Icons.MAIL_OUTLINE_ROUNDED,
                        "Contact developer",
                        CONTACT_EMAIL,
                        f"mailto:{CONTACT_EMAIL}",
                    ),
                    _row(
                        ft.Icons.STAR_ROUNDED,
                        "Rate 5 stars",
                        "Rate us on Google Play" if store else "Star us on GitHub",
                        KIRI_APPS_PLAY_URL if store else GITHUB_REPO_URL,
                    ),
                    _row(
                        ft.Icons.APPS_ROUNDED,
                        "More apps from Kiri",
                        "All our apps on Google Play"
                        if store
                        else "Asase, Sherlock, DDGS and more",
                        KIRI_APPS_PLAY_URL if store else KIRI_APPS_URL,
                    ),
                    ft.Container(height=tokens.SPACE_XS),
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
                                    schedule(
                                        state.ad_service.show_privacy_options,
                                        page=page,
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
