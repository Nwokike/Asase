"""Section Header component for grouping dashboard and settings cards."""

import flet as ft

from core import tokens
from core.theme import AppColors


def SectionHeader(title: str) -> ft.Container:
    """Build a styled section header with uppercase badge style."""
    return ft.Container(
        content=ft.Text(
            title.upper(),
            size=tokens.FONT_XS,
            weight=ft.FontWeight.W_700,
            color=AppColors.PRIMARY,
            font_family="Outfit",
        ),
        padding=ft.Padding(
            left=tokens.SPACE_XL,
            right=tokens.SPACE_XL,
            top=tokens.SPACE_MD,
            bottom=tokens.SPACE_XS,
        ),
    )
