"""Single boot screen replacing the 3-slide onboarding deck.

One modern loading view: brand logo, live init progress driven by the
controller's loading_message, then auto-dismiss when telemetry lands.
No Next/Skip/dots — first launch and every cold start share it. On web
(Pyodide) it also covers the interpreter load, which is the entire
reason a boot screen exists here.
"""

from __future__ import annotations

import flet as ft
from flet import Control

from core import tokens
from core.theme import AppColors, build_logo
from state.app_state import AppStateCtx


def build_boot_view(
    loading_message: str | None,
    progress: float | None = None,
) -> Control:
    """Pure boot view (testable): logo + message + progress bar."""
    return ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=[
                ft.Colors.SURFACE,
                ft.Colors.with_opacity(0.06, AppColors.PRIMARY),
            ],
        ),
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                ft.Container(expand=True),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=tokens.SPACE_MD,
                    controls=[
                        build_logo(height=84),
                        ft.Text(
                            "ASASE",
                            size=tokens.FONT_XXL,
                            weight=ft.FontWeight.W_800,
                            color=AppColors.PRIMARY,
                        ),
                        ft.Text(
                            "GLOBAL EARTH INTELLIGENCE",
                            size=tokens.FONT_XS,
                            weight=ft.FontWeight.W_700,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        ft.Container(height=tokens.SPACE_MD),
                        ft.Container(
                            content=ft.ProgressBar(
                                value=progress,
                                color=AppColors.PRIMARY,
                                bgcolor=ft.Colors.with_opacity(0.15, AppColors.PRIMARY),
                            ),
                            width=220,
                        ),
                        ft.Text(
                            loading_message or "Initializing planetary telemetry…",
                            size=tokens.FONT_SM,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                ),
                ft.Container(expand=True),
                ft.Text(
                    "Live USGS • NASA • NOAA • Open-Meteo — no account required",
                    size=tokens.FONT_XXS,
                    color=ft.Colors.with_opacity(
                        tokens.OPACITY_DIM, ft.Colors.ON_SURFACE
                    ),
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(height=tokens.SPACE_LG),
            ],
        ),
    )


@ft.component
def BootScreen() -> Control:
    state = ft.use_context(AppStateCtx)

    _ = (state.is_loading, state.loading_message, state.telemetry_version)
    progress = 0.3 if state.is_loading else 1.0
    return build_boot_view(state.loading_message, progress=progress)


__all__ = ["BootScreen", "build_boot_view"]
