"""Section Header component for grouping dashboard and settings cards."""

from __future__ import annotations

from collections.abc import Callable

import flet as ft

from core import tokens
from core.theme import AppColors


def SectionHeader(
    title: str,
    action_text: str | None = None,
    on_action: Callable | None = None,
) -> ft.Container:
    """Build a styled section header with optional trailing action button."""
    header_text = ft.Text(
        title.upper(),
        size=tokens.FONT_XS,
        weight=ft.FontWeight.W_700,
        color=AppColors.PRIMARY,
        font_family="Outfit",
    )

    if action_text and on_action:
        action_btn = ft.TextButton(
            content=ft.Row(
                [
                    ft.Text(
                        action_text.upper(),
                        size=tokens.FONT_XXS,
                        weight=ft.FontWeight.W_700,
                        color=AppColors.PRIMARY,
                    ),
                    ft.Icon(
                        ft.Icons.ARROW_FORWARD_IOS_ROUNDED,
                        size=10,
                        color=AppColors.PRIMARY,
                    ),
                ],
                spacing=2,
                tight=True,
            ),
            on_click=on_action,
            style=ft.ButtonStyle(
                padding=ft.Padding(4, 2, 4, 2),
            ),
        )
        content_row = ft.Row(
            [header_text, action_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )
        return ft.Container(
            content=content_row,
            padding=ft.Padding(
                left=tokens.SPACE_XL,
                right=tokens.SPACE_XL,
                top=tokens.SPACE_MD,
                bottom=tokens.SPACE_XS,
            ),
        )

    return ft.Container(
        content=header_text,
        padding=ft.Padding(
            left=tokens.SPACE_XL,
            right=tokens.SPACE_XL,
            top=tokens.SPACE_MD,
            bottom=tokens.SPACE_XS,
        ),
    )
