"""Report AI Risk Briefing section — grounded Kiri Gateway narration."""

from __future__ import annotations

import logging

import flet as ft

from core import tokens
from core.theme import AppColors, AppStyles
from services.ai_service import DEFAULT_QUESTION, stream_briefing

logger = logging.getLogger("asase.report.ai")


def build_ai_briefing_section(
    answer: str,
    busy: bool,
    unavailable: bool,
    question: str,
    on_generate,
    on_ask,
    on_question_change,
) -> ft.Container:
    """Builds the grounded AI briefing card (Generate + follow-up Ask)."""
    return ft.Container(
        content=AppStyles.glass_card(
            ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(
                                    ft.Icons.PSYCHOLOGY_ROUNDED,
                                    size=tokens.ICON_MD,
                                    color=AppColors.ATMOSPHERE,
                                ),
                                width=tokens.ICON_BACKDROP,
                                height=tokens.ICON_BACKDROP,
                                border_radius=tokens.ICON_BACKDROP_RADIUS,
                                bgcolor=ft.Colors.with_opacity(
                                    tokens.OPACITY_LIGHT, AppColors.ATMOSPHERE
                                ),
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        "Kiri Intelligence",
                                        size=tokens.FONT_MD,
                                        weight=ft.FontWeight.W_600,
                                        font_family="Outfit",
                                    ),
                                    ft.Text(
                                        "AI risk briefing grounded on the live measured telemetry above — no invented data.",
                                        size=tokens.FONT_XS,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                                spacing=tokens.SPACE_XXS,
                                expand=True,
                            ),
                        ],
                        spacing=tokens.SPACE_MD,
                    ),
                    *(
                        [
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.ProgressRing(
                                            width=18, height=18, stroke_width=2
                                        ),
                                        ft.Text(
                                            "Analyzing live telemetry...",
                                            size=tokens.FONT_XS,
                                            color=ft.Colors.ON_SURFACE_VARIANT,
                                        ),
                                    ],
                                    spacing=tokens.SPACE_SM,
                                ),
                                padding=tokens.SPACE_MD,
                                alignment=ft.Alignment.CENTER,
                            )
                        ]
                        if busy and not answer
                        else []
                    ),
                    *(
                        [
                            ft.Container(
                                content=ft.Text(
                                    answer,
                                    size=tokens.FONT_SM,
                                    selectable=True,
                                ),
                                padding=tokens.SPACE_MD,
                                border_radius=tokens.RADIUS_MD,
                                bgcolor=ft.Colors.with_opacity(
                                    0.06, AppColors.ATMOSPHERE
                                ),
                                border=ft.Border.all(
                                    1,
                                    ft.Colors.with_opacity(0.2, AppColors.ATMOSPHERE),
                                ),
                            )
                        ]
                        if answer
                        else []
                    ),
                    *(
                        [
                            ft.Text(
                                "AI briefing unavailable right now — the measured telemetry above is unaffected.",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            )
                        ]
                        if unavailable and not busy and not answer
                        else []
                    ),
                    ft.Container(height=tokens.SPACE_XS),
                    ft.Row(
                        [
                            ft.FilledButton(
                                icon=ft.Icons.AUTO_AWESOME_ROUNDED,
                                content=ft.Text(
                                    "Regenerate Briefing"
                                    if answer
                                    else "Generate Briefing",
                                    size=tokens.FONT_SM,
                                    weight=ft.FontWeight.W_600,
                                    color=ft.Colors.WHITE,
                                ),
                                style=ft.ButtonStyle(
                                    bgcolor=AppColors.ATMOSPHERE,
                                    shape=ft.RoundedRectangleBorder(
                                        radius=tokens.RADIUS_MD
                                    ),
                                ),
                                on_click=on_generate,
                                disabled=busy,
                            ),
                        ],
                        spacing=tokens.SPACE_SM,
                    ),
                    *(
                        [
                            ft.Container(height=tokens.SPACE_XS),
                            ft.TextField(
                                value=question,
                                hint_text="Ask a follow-up about this location...",
                                border_radius=tokens.RADIUS_MD,
                                text_size=tokens.FONT_SM,
                                content_padding=tokens.SPACE_SM,
                                on_submit=on_ask,
                                on_change=on_question_change,
                            ),
                        ]
                        if answer and not busy
                        else []
                    ),
                ],
                spacing=tokens.SPACE_XS,
            ),
            padding=tokens.SPACE_MD,
        ),
        padding=ft.Padding(tokens.SPACE_LG, 0, tokens.SPACE_LG, 0),
    )


__all__ = [
    "DEFAULT_QUESTION",
    "build_ai_briefing_section",
    "stream_briefing",
]
