"""Empty-state illustration + title + CTA — shared pattern from DDGS/Sherlock."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors


def EmptyState(
    icon: ft.IconData = ft.Icons.SEARCH_OFF_ROUNDED,
    title: str = "Nothing here yet",
    subtitle: str = "Try a different search or check back later.",
    action_text: str | None = None,
    on_action: Callable | None = None,
) -> ft.Control:
    return ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ft.Icon(icon, size=48, color=AppColors.GREY),
                    width=72,
                    height=72,
                    border_radius=36,
                    bgcolor=ft.Colors.with_opacity(0.08, AppColors.GREY),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(
                    title,
                    size=tokens.FONT_MD,
                    weight=ft.FontWeight.W_600,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    subtitle,
                    size=tokens.FONT_SM,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=3,
                ),
                *(
                    [
                        ft.FilledButton(
                            content=ft.Text(action_text),
                            on_click=lambda _: on_action() if on_action else None,
                        )
                    ]
                    if action_text and on_action
                    else []
                ),
            ],
            spacing=tokens.SPACE_SM,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=tokens.SPACE_XL,
        alignment=ft.Alignment.CENTER,
    )
