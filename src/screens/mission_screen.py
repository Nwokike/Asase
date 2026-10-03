"""First-run mission: 3-step checklist shown after boot dismisses.

Replaces the passive boot wait with an active onboarding mission.
Each step is tappable and navigates to the right screen.
Persisted as "shown" in storage so it only appears once.
"""

from __future__ import annotations

import logging

import flet as ft
from flet import Control
from flet import context as flet_context

from core import tokens
from core.constants import STORAGE_MISSION_SHOWN
from core.tasks import schedule
from core.theme import AppColors
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.mission")

_MISSION_STEPS = [
    {
        "icon": ft.Icons.PUBLIC_ROUNDED,
        "title": "Tap a hazard on the map",
        "subtitle": "See live seismic, wildfire, and storm events",
        "action": "Open Map",
    },
    {
        "icon": ft.Icons.ASSESSMENT_ROUNDED,
        "title": "Open a location dossier",
        "subtitle": "Get a full multi-hazard risk assessment",
        "action": "Open Dossier",
    },
    {
        "icon": ft.Icons.PSYCHOLOGY_ROUNDED,
        "title": "Run an AI map scan",
        "subtitle": "Let AI analyze the visible hazard patterns",
        "action": "Run AI Scan",
    },
]


def build_mission_view(
    step: int,
    on_advance,
    on_dismiss,
) -> Control:
    """Pure mission view (testable): step content + progress dots."""
    current = _MISSION_STEPS[min(step, len(_MISSION_STEPS) - 1)]
    is_last = step >= len(_MISSION_STEPS) - 1

    dots = [
        ft.Container(
            width=8 if i == step else 6,
            height=8,
            border_radius=4,
            bgcolor=AppColors.PRIMARY
            if i <= step
            else ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE),
        )
        for i in range(len(_MISSION_STEPS))
    ]

    return ft.Container(
        content=ft.Column(
            [
                ft.Container(expand=True),
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=tokens.SPACE_MD,
                    controls=[
                        ft.Icon(
                            current["icon"],
                            size=56,
                            color=AppColors.PRIMARY,
                        ),
                        ft.Text(
                            f"Step {step + 1} of {len(_MISSION_STEPS)}",
                            size=tokens.FONT_XXS,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            weight=ft.FontWeight.W_600,
                        ),
                        ft.Text(
                            current["title"],
                            size=tokens.FONT_LG,
                            weight=ft.FontWeight.W_700,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Text(
                            current["subtitle"],
                            size=tokens.FONT_SM,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ],
                ),
                ft.Container(height=tokens.SPACE_MD),
                ft.Row(
                    dots,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=tokens.SPACE_XS,
                ),
                ft.Container(height=tokens.SPACE_MD),
                ft.FilledButton(
                    content=ft.Text(
                        "Done" if is_last else current["action"],
                        size=tokens.FONT_SM,
                        weight=ft.FontWeight.W_600,
                    ),
                    on_click=lambda _: on_advance(),
                    expand=True,
                    height=48,
                ),
                ft.TextButton(
                    content=ft.Text(
                        "Skip mission",
                        size=tokens.FONT_XS,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    on_click=lambda _: on_dismiss(),
                ),
                ft.Container(expand=True),
            ],
            spacing=0,
            expand=True,
        ),
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=[
                ft.Colors.SURFACE,
                ft.Colors.with_opacity(0.04, AppColors.PRIMARY),
            ],
        ),
        padding=ft.Padding(
            tokens.SPACE_LG, tokens.SPACE_XL, tokens.SPACE_LG, tokens.SPACE_XL
        ),
    )


@ft.component
def MissionScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    step, set_step = ft.use_state(state.mission_step)
    is_dark = True  # mission is always dark for focus

    def _advance():
        next_step = step + 1
        if next_step >= len(_MISSION_STEPS):
            _dismiss()
            return
        state.mission_step = next_step
        set_step(next_step)
        # Navigate to the relevant screen for this step
        page = flet_context.page
        if next_step == 0 and controller.show_map:
            schedule(controller.show_map, page=page)
        elif next_step == 1 and controller.open_report:
            schedule(controller.open_report, page=page)
        # Step 2 (AI scan) is on the map screen — user taps the pill there

    def _dismiss():
        state.mission_shown = True
        state.mission_step = 0
        page = flet_context.page
        if controller.save_setting:
            schedule(
                controller.save_setting,
                STORAGE_MISSION_SHOWN,
                "true",
                page=page,
            )
        if controller.go_home:
            schedule(controller.go_home, page=page)

    _ = (is_dark, state.mission_shown)
    return build_mission_view(step, _advance, _dismiss)


__all__ = ["MissionScreen", "build_mission_view"]
