"""Tests for Design Tokens and Theme."""

import flet as ft

from core import tokens
from core.theme import AppColors, AppTheme, is_dark_mode


def test_tokens_spacing_progression():
    assert (
        tokens.SPACE_XXS
        < tokens.SPACE_XS
        < tokens.SPACE_SM
        < tokens.SPACE_MD
        < tokens.SPACE_LG
        < tokens.SPACE_XL
    )


def test_tokens_typography_scale():
    assert (
        tokens.FONT_XXS
        < tokens.FONT_XS
        < tokens.FONT_SM
        < tokens.FONT_MD
        < tokens.FONT_LG
        < tokens.FONT_XL
        < tokens.FONT_XXL
    )


def test_theme_generation(mock_page):
    light_theme = AppTheme.get_light_theme()
    dark_theme = AppTheme.get_dark_theme()

    assert light_theme is not None
    assert dark_theme is not None
    assert light_theme.color_scheme.primary == AppColors.PRIMARY
    assert dark_theme.color_scheme.primary == AppColors.PRIMARY


def test_is_dark_mode_helper(mock_page):
    mock_page.theme_mode = ft.ThemeMode.DARK
    assert is_dark_mode(mock_page) is True

    mock_page.theme_mode = ft.ThemeMode.LIGHT
    assert is_dark_mode(mock_page) is False
