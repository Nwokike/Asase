"""Theme & Palette definition for Asase.

Earth-intelligence themed: Slate & Obsidian dark background, Emerald Green
(Life on Land), Oceanic Cyan (Hydrology/Marine), Amber (Warning), and
Crimson (Severe Hazard Alert).
"""

from __future__ import annotations

import flet as ft

from core import tokens


class AppColors:
    # Earth Intelligence Accents
    PRIMARY = "#10B981"  # Emerald 500 (Land Health & Primary Brand)
    PRIMARY_LIGHT = "#34D399"  # Emerald 400
    PRIMARY_DARK = "#059669"  # Emerald 600

    OCEAN = "#0EA5E9"  # Sky/Ocean 500 (Hydrology & Marine)
    OCEAN_LIGHT = "#38BDF8"  # Sky 400

    ATMOSPHERE = "#8B5CF6"  # Violet 500 (Space Weather & Geomagnetism)

    # Hazard Severity Spectrum
    SEVERITY_LOW = "#10B981"  # Safe / Normal (Green)
    SEVERITY_MODERATE = "#F59E0B"  # Advisory / Moderate (Amber)
    SEVERITY_HIGH = "#F97316"  # Warning / High (Orange)
    SEVERITY_CRITICAL = "#EF4444"  # Critical / Disaster (Red)

    SUCCESS = "#10B981"
    WARNING = "#F59E0B"
    ERROR = "#EF4444"
    INFO = "#0EA5E9"
    GREY = "#64748B"

    # Dark Surface System
    DARK_BG = "#0B0F17"  # Deep Obsidian Space
    DARK_SURFACE = "#111827"  # Slate Surface
    DARK_SURFACE_2 = "#1E293B"  # Elevated Slate
    DARK_SURFACE_3 = "#334155"  # Card Highlight Border
    DARK_TEXT = "#F8FAFC"
    DARK_MUTED = "#94A3B8"

    # Light Surface System
    LIGHT_BG = "#F8FAFC"
    LIGHT_SURFACE = "#FFFFFF"
    LIGHT_SURFACE_2 = "#F1F5F9"
    LIGHT_SURFACE_3 = "#E2E8F0"
    LIGHT_TEXT = "#0F172A"
    LIGHT_MUTED = "#64748B"


def is_dark_mode(page: ft.Page | None) -> bool:
    if not page:
        return True
    if page.theme_mode == ft.ThemeMode.DARK:
        return True
    if page.theme_mode == ft.ThemeMode.LIGHT:
        return False
    return getattr(page.platform_brightness, "value", "dark") == "dark"


def adaptive_glass_bg(page: ft.Page | None = None) -> str:
    dark = is_dark_mode(page)
    return AppColors.DARK_SURFACE_2 if dark else AppColors.LIGHT_SURFACE


def adaptive_glass_border(page: ft.Page | None = None) -> str:
    dark = is_dark_mode(page)
    return (
        ft.Colors.with_opacity(0.12, ft.Colors.WHITE)
        if dark
        else ft.Colors.with_opacity(0.12, ft.Colors.BLACK)
    )


class AppTheme:
    @staticmethod
    def get_light_theme() -> ft.Theme:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=AppColors.PRIMARY,
                on_primary=ft.Colors.WHITE,
                primary_container="#D1FAE5",
                on_primary_container="#065F46",
                secondary=AppColors.OCEAN,
                on_secondary=ft.Colors.WHITE,
                surface=AppColors.LIGHT_SURFACE,
                on_surface=AppColors.LIGHT_TEXT,
                on_surface_variant=AppColors.LIGHT_MUTED,
                outline=AppColors.LIGHT_SURFACE_3,
                error=AppColors.ERROR,
                error_container="#FEE2E2",
                on_error_container="#991B1B",
            ),
            font_family="Outfit",
        )

    @staticmethod
    def get_dark_theme() -> ft.Theme:
        return ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=AppColors.PRIMARY,
                on_primary="#064E3B",
                primary_container="#065F46",
                on_primary_container="#D1FAE5",
                secondary=AppColors.OCEAN_LIGHT,
                on_secondary="#082F49",
                surface=AppColors.DARK_SURFACE,
                on_surface=AppColors.DARK_TEXT,
                on_surface_variant=AppColors.DARK_MUTED,
                outline=AppColors.DARK_SURFACE_3,
                error=AppColors.ERROR,
                error_container="#7F1D1D",
                on_error_container="#FEE2E2",
            ),
            font_family="Outfit",
        )


class AppStyles:
    @staticmethod
    def glass_card(
        content: ft.Control,
        page: ft.Page | None = None,
        padding: float | ft.Padding = tokens.SPACE_MD,
        on_click=None,
    ) -> ft.Container:
        return ft.Container(
            content=content,
            padding=padding,
            border_radius=tokens.RADIUS_LG,
            bgcolor=adaptive_glass_bg(page),
            border=ft.Border.all(1, adaptive_glass_border(page)),
            ink=on_click is not None,
            on_click=on_click,
            animate=ft.Animation(tokens.ANIM_FAST, "easeOut"),
        )
