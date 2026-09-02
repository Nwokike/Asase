"""OnboardingScreen — first-launch 3-slide showcase deck (Sherlock pattern).

Simple and theme-reactive by design: every color is a Material surface token
(dark mode dark, light mode light) over the family gradient (SURFACE → 6%
PRIMARY). No forms, no live panels — the dashboard search bar handles
locality; onboarding just shows what Asase does.
"""

from __future__ import annotations

import asyncio
import contextlib

import flet as ft
from flet import Control

from core import tokens
from core.constants import STORAGE_ONBOARDING_DONE
from core.theme import AppColors, build_logo, is_dark_mode
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

_HERO_ICON = 56  # family-standard onboarding hero icon size (Sherlock ICON_FEATURE)


def _build_brand_slide(page) -> ft.Column:
    """Slide 1 — reactive wordmark (never squeezed into an icon badge)."""
    return ft.Column(
        [
            build_logo(page, height=72),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
    )


def _hero_icon(icon, color: str) -> ft.Container:
    is_dark = is_dark_mode(None)
    return ft.Container(
        content=ft.Icon(icon, size=_HERO_ICON, color=color),
        width=_HERO_ICON + 54,
        height=_HERO_ICON + 54,
        border_radius=(_HERO_ICON + 54) // 2,
        bgcolor=ft.Colors.with_opacity(
            tokens.OPACITY_SUBTLE,
            (ft.Colors.WHITE if is_dark else color),
        ),
        alignment=ft.Alignment.CENTER,
    )


def _build_hazards_slide() -> ft.Column:
    """Slide 2 — the multi-hazard command view."""
    return ft.Column(
        [
            _hero_icon(ft.Icons.PUBLIC_ROUNDED, AppColors.OCEAN),
            ft.Container(height=tokens.SPACE_XL),
            ft.Text(
                "Every Hazard,\nOne Command View",
                size=tokens.FONT_XXL,
                weight=ft.FontWeight.W_800,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.ON_SURFACE,
                font_family="Outfit",
            ),
            ft.Container(height=tokens.SPACE_MD),
            ft.Text(
                "Live USGS earthquakes, NASA wildfires and severe storms, river "
                "floods, and air quality — fused onto one interactive map with "
                "geodesic shockwave radii.",
                size=tokens.FONT_MD,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
                font_family="Outfit",
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
    )


def _build_ai_slide() -> ft.Column:
    """Slide 3 — grounded AI briefings."""
    return ft.Column(
        [
            _hero_icon(ft.Icons.PSYCHOLOGY_ROUNDED, AppColors.PRIMARY),
            ft.Container(height=tokens.SPACE_XL),
            ft.Text(
                "Grounded AI\nBriefings",
                size=tokens.FONT_XXL,
                weight=ft.FontWeight.W_800,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.ON_SURFACE,
                font_family="Outfit",
            ),
            ft.Container(height=tokens.SPACE_MD),
            ft.Text(
                "Plain-language risk dossiers for any point on Earth, "
                "synthesized from measured telemetry via Kiri Intelligence — "
                "strictly zero hallucinations.",
                size=tokens.FONT_MD,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
                font_family="Outfit",
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
    )


def build_onboarding_view(
    page: ft.Page | None,
    page_idx: int,
    on_next,
    on_skip,
    on_swipe,
    on_dot_click,
) -> Control:
    """Builds the showcase deck for the given slide index (testable)."""
    is_last = page_idx == 2

    if page_idx == 0:
        middle = _build_brand_slide(page)
    elif page_idx == 1:
        middle = _build_hazards_slide()
    else:
        middle = _build_ai_slide()

    # Dot indicators (tappable, active dot stretches into a pill)
    dots = [
        ft.GestureDetector(
            content=ft.Container(
                width=24 if i == page_idx else 8,
                height=8,
                border_radius=4,
                bgcolor=AppColors.PRIMARY
                if i == page_idx
                else ft.Colors.with_opacity(
                    tokens.OPACITY_MEDIUM, ft.Colors.ON_SURFACE
                ),
                animate=ft.Animation(tokens.ANIM_SLOW, "easeOut"),
            ),
            on_tap=lambda e, idx=i: on_dot_click(idx),
        )
        for i in range(3)
    ]

    cta_label = "Enter Planetary Command" if is_last else "Next"

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
                # Top bar — Skip button (hidden on last slide)
                ft.Container(
                    padding=ft.Padding(
                        tokens.SPACE_LG, tokens.SPACE_MD, tokens.SPACE_LG, 0
                    ),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.TextButton(
                                "Skip",
                                visible=not is_last,
                                on_click=on_skip,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ),
                        ],
                    ),
                ),
                # Middle — swipeable slide content fills all remaining space
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.GestureDetector(
                        content=ft.Container(
                            content=middle,
                            alignment=ft.Alignment.CENTER,
                            padding=ft.Padding(tokens.SPACE_XL, 0, tokens.SPACE_XL, 0),
                        ),
                        on_horizontal_drag_end=on_swipe,
                    ),
                ),
                # Bottom — dots + CTA + disclaimer pinned to bottom
                ft.Container(
                    padding=ft.Padding(
                        tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_LG
                    ),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=tokens.SPACE_MD,
                        controls=[
                            ft.Row(
                                controls=dots,
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=tokens.SPACE_SM,
                            ),
                            ft.FilledButton(
                                content=ft.Text(
                                    cta_label,
                                    size=tokens.FONT_MD,
                                    weight=ft.FontWeight.W_600,
                                    font_family="Outfit",
                                    color=ft.Colors.WHITE,
                                ),
                                icon=ft.Icons.ROCKET_LAUNCH_ROUNDED
                                if is_last
                                else ft.Icons.ARROW_FORWARD_ROUNDED,
                                on_click=on_next,
                                width=340,
                                height=52,
                                style=ft.ButtonStyle(
                                    bgcolor=AppColors.PRIMARY,
                                    shape=ft.RoundedRectangleBorder(
                                        radius=tokens.RADIUS_XL
                                    ),
                                ),
                            ),
                            ft.Text(
                                "Live telemetry from USGS, NASA, NOAA, Copernicus & "
                                "Open-Meteo. No account required.",
                                size=tokens.FONT_XXS,
                                color=ft.Colors.with_opacity(
                                    tokens.OPACITY_DIM, ft.Colors.ON_SURFACE
                                ),
                                text_align=ft.TextAlign.CENTER,
                                max_lines=2,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )


@ft.component
def OnboardingScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)
    page_idx, set_page_idx = ft.use_state(0)

    from flet import context as flet_context

    page = flet_context.page

    is_last = page_idx == 2

    async def _finish():
        state.has_accepted_terms = True
        state.is_first_launch = False
        state.telemetry_version += 1
        if controller.dismiss_onboarding:
            controller.dismiss_onboarding()
        if controller.save_setting:
            await controller.save_setting(STORAGE_ONBOARDING_DONE, "true")

    def _tap_haptic():
        with contextlib.suppress(Exception):
            asyncio.create_task(ft.HapticFeedback().light_impact())

    def _on_next(e=None):
        _tap_haptic()
        if is_last:
            asyncio.create_task(_finish())
        else:
            set_page_idx(page_idx + 1)

    def _on_skip(e):
        _tap_haptic()
        asyncio.create_task(_finish())

    def _on_swipe(e: ft.DragEndEvent):
        if e.primary_velocity is not None:
            if e.primary_velocity < -200 and not is_last:
                _tap_haptic()
                set_page_idx(page_idx + 1)
            elif e.primary_velocity > 200 and page_idx > 0:
                _tap_haptic()
                set_page_idx(page_idx - 1)

    def _on_dot_click(idx: int):
        _tap_haptic()
        set_page_idx(idx)

    return build_onboarding_view(
        page, page_idx, _on_next, _on_skip, _on_swipe, _on_dot_click
    )


__all__ = ["OnboardingScreen", "build_onboarding_view"]
