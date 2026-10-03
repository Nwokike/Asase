"""Adaptive navigation chrome for Asase (web-primary, Android secondary).

M3 window-size classes drive the chrome:
- Compact  (<600px): bottom NavigationBar (existing, untouched behavior).
- Medium   (600-840px): icon NavigationRail.
- Expanded (>840px): collapsible sidebar (264px labels <-> 72px rail),
  collapse state persisted per device via STORAGE_SIDEBAR_COLLAPSED.

The tab+view state machine is unchanged — this file only renders chrome
for it. All Flet APIs verified against flet 1.0.3 installed source:
NavigationRail(destinations, selected_index, on_change, extended,
min_width), NavigationRailDestination(icon, selected_icon, label),
View.drawer + page.show_drawer(), page.width + page.on_resize.
"""

from __future__ import annotations

import logging

import flet as ft

from core import tokens
from core.theme import AppColors, build_logo, is_dark_mode

logger = logging.getLogger("asase.nav")

# (tab index, label, icon, selected icon)
NAV_ITEMS: tuple[tuple[int, str, ft.IconData, ft.IconData], ...] = (
    (0, "Radar", ft.Icons.DASHBOARD_OUTLINED, ft.Icons.DASHBOARD_ROUNDED),
    (1, "Full Map", ft.Icons.MAP_OUTLINED, ft.Icons.MAP_ROUNDED),
    (2, "Space", ft.Icons.PUBLIC_OUTLINED, ft.Icons.PUBLIC_ROUNDED),
    (3, "History", ft.Icons.HISTORY_OUTLINED, ft.Icons.HISTORY_ROUNDED),
    (4, "Settings", ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS_ROUNDED),
)


def window_class(width: float | None) -> str:
    """M3 window-size class for a viewport width. Unknown width → compact
    (bottom nav is the safe default on phones)."""
    if width is None:
        return "compact"
    if width < tokens.WINDOW_COMPACT_MAX + 1:
        return "compact"
    if width <= tokens.WINDOW_MEDIUM_MAX:
        return "medium"
    return "expanded"


def build_navigation_bar(active_tab: int, on_select) -> ft.NavigationBar:
    """Compact chrome: bottom navigation bar (existing behavior)."""
    return ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon=icon, selected_icon=selected, label=label)
            for _, label, icon, selected in NAV_ITEMS
        ],
        selected_index=active_tab,
        on_change=on_select,
        indicator_color=ft.Colors.with_opacity(0.2, AppColors.PRIMARY),
    )


def build_navigation_rail(active_tab: int, on_select) -> ft.NavigationRail:
    """Medium chrome: icon rail with labels."""
    return ft.NavigationRail(
        destinations=[
            ft.NavigationRailDestination(icon=icon, selected_icon=selected, label=label)
            for _, label, icon, selected in NAV_ITEMS
        ],
        selected_index=active_tab,
        on_change=on_select,
        group_alignment=-1.0,
        indicator_color=ft.Colors.with_opacity(0.2, AppColors.PRIMARY),
    )


def build_sidebar(
    active_tab: int,
    on_select,
    collapsed: bool,
    on_toggle_collapse,
    footer: ft.Control | None = None,
) -> ft.Container:
    """Expanded chrome: full labeled sidebar <-> collapsed icon rail.

    A custom column (not NavigationRail.extended) so the collapse toggle,
    branding header, and footer slot render identically in both states.
    """
    rows: list[ft.Control] = []
    for idx, label, icon, selected in NAV_ITEMS:
        is_active = idx == active_tab
        rows.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(
                            selected if is_active else icon,
                            size=tokens.ICON_MD,
                            color=AppColors.PRIMARY
                            if is_active
                            else ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        *(
                            [
                                ft.Text(
                                    label,
                                    size=tokens.FONT_SM,
                                    weight=ft.FontWeight.W_600
                                    if is_active
                                    else ft.FontWeight.W_500,
                                    color=AppColors.PRIMARY
                                    if is_active
                                    else ft.Colors.ON_SURFACE,
                                )
                            ]
                            if not collapsed
                            else []
                        ),
                    ],
                    spacing=tokens.SPACE_MD,
                    tight=True,
                ),
                padding=ft.Padding(
                    tokens.SPACE_MD, tokens.SPACE_SM, tokens.SPACE_MD, tokens.SPACE_SM
                ),
                border_radius=tokens.RADIUS_MD,
                bgcolor=ft.Colors.with_opacity(0.12, AppColors.PRIMARY)
                if is_active
                else None,
                ink=True,
                on_click=lambda _, i=idx: on_select(i),
            )
        )
    body = ft.Column(
        [
            ft.Container(
                content=ft.Row(
                    [
                        *(
                            [build_logo(height=30)]
                            if not collapsed
                            else [
                                ft.Image(
                                    src="/icon.svg",
                                    width=28,
                                    height=28,
                                    color=ft.Colors.WHITE if is_dark_mode() else None,
                                )
                            ]
                        ),
                        ft.IconButton(
                            icon=ft.Icons.MENU_OPEN_ROUNDED
                            if not collapsed
                            else ft.Icons.MENU_ROUNDED,
                            tooltip="Collapse sidebar"
                            if not collapsed
                            else "Expand sidebar",
                            icon_color=ft.Colors.ON_SURFACE_VARIANT,
                            on_click=lambda _: on_toggle_collapse(),
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    if not collapsed
                    else ft.MainAxisAlignment.CENTER,
                ),
                padding=ft.Padding(tokens.SPACE_MD, tokens.SPACE_SM, 0, 0),
            ),
            ft.Container(height=tokens.SPACE_SM),
            *rows,
            ft.Container(expand=True),
            *([footer] if footer is not None else []),
        ],
        spacing=tokens.SPACE_XS,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
    return ft.Container(
        content=body,
        width=tokens.SIDEBAR_RAIL_WIDTH if collapsed else tokens.SIDEBAR_EXPANDED_WIDTH,
        bgcolor=AppColors.get_surface(),
        border=ft.Border(
            right=ft.BorderSide(1, AppColors.get_border()),
        ),
        padding=ft.Padding(
            tokens.SPACE_SM, tokens.SPACE_SM, tokens.SPACE_SM, tokens.SPACE_SM
        ),
        animate=ft.Animation(tokens.ANIM_NORMAL, ft.AnimationCurve.EASE_OUT),
    )


def build_status_bar(
    location_name: str,
    alert_count: int,
    kp_text: str,
    on_command_palette,
    is_dark: bool = True,
    title: str | None = None,
    subtitle: str | None = None,
    on_refresh=None,
    on_settings=None,
    on_toggle_theme=None,
    theme_icon: ft.IconData | None = None,
    theme_tooltip: str | None = None,
    on_open_version=None,
    version_label: str | None = None,
    update_available: bool = False,
) -> ft.Container:
    """Top status bar for medium/expanded windows: live context at a glance.

    Absorbs the old per-screen AppHeader: screen title/subtitle, refresh,
    settings gear, theme toggle, and version/update chip all live here and
    change per active screen — screens no longer render their own header.
    """
    actions: list[ft.Control] = []
    if version_label or update_available:
        dot = (
            ft.Container(
                width=6,
                height=6,
                border_radius=3,
                bgcolor=AppColors.PRIMARY,
            )
            if update_available
            else None
        )
        actions.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            version_label or "",
                            size=tokens.FONT_XS,
                            weight=ft.FontWeight.BOLD,
                            color=AppColors.PRIMARY
                            if update_available
                            else ft.Colors.ON_SURFACE_VARIANT,
                            no_wrap=True,
                        ),
                        *([dot] if dot is not None else []),
                    ],
                    spacing=6,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding(10, 4, 10, 4),
                border_radius=10,
                bgcolor=ft.Colors.with_opacity(
                    0.15 if update_available else 0.08,
                    AppColors.PRIMARY
                    if update_available
                    else ft.Colors.ON_SURFACE_VARIANT,
                ),
                ink=True,
                tooltip="What's New — version & changelog",
                on_click=lambda _: on_open_version() if on_open_version else None,
            )
        )
    if on_toggle_theme and theme_icon:
        actions.append(
            ft.IconButton(
                icon=theme_icon,
                icon_size=20,
                tooltip=theme_tooltip or "Toggle Color Mode",
                on_click=lambda _: on_toggle_theme(),
            )
        )
    if on_refresh:
        actions.append(
            ft.IconButton(
                icon=ft.Icons.REFRESH_ROUNDED,
                icon_size=20,
                tooltip="Sync Live Feeds",
                on_click=lambda _: on_refresh(),
            )
        )
    if on_settings:
        actions.append(
            ft.IconButton(
                icon=ft.Icons.SETTINGS_OUTLINED,
                icon_size=20,
                tooltip="Settings",
                on_click=lambda _: on_settings(),
            )
        )
    return ft.Container(
        content=ft.Row(
            [
                *(
                    [
                        ft.Column(
                            [
                                ft.Text(
                                    title or location_name or "Global Telemetry",
                                    size=tokens.FONT_MD,
                                    weight=ft.FontWeight.BOLD,
                                    max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                ),
                                ft.Text(
                                    (subtitle or "EARTH INTELLIGENCE").upper(),
                                    size=tokens.FONT_XXS,
                                    weight=ft.FontWeight.W_700,
                                    color=AppColors.PRIMARY,
                                    max_lines=1,
                                ),
                            ],
                            spacing=0,
                            expand=True,
                        )
                    ]
                    if (title or subtitle)
                    else [
                        ft.Icon(
                            ft.Icons.SATELLITE_ALT_ROUNDED,
                            size=tokens.ICON_SM,
                            color=AppColors.PRIMARY,
                        ),
                        ft.Text(
                            location_name or "Global Telemetry",
                            size=tokens.FONT_SM,
                            weight=ft.FontWeight.W_600,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                    ]
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.WARNING_AMBER_ROUNDED,
                                size=tokens.ICON_XS,
                                color=AppColors.WARNING
                                if alert_count
                                else ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Text(
                                f"{alert_count} alerts",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=tokens.SPACE_XXS,
                        tight=True,
                    ),
                    border_radius=tokens.RADIUS_FULL,
                    padding=ft.Padding(
                        tokens.SPACE_SM,
                        tokens.SPACE_XS,
                        tokens.SPACE_SM,
                        tokens.SPACE_XS,
                    ),
                    bgcolor=ft.Colors.with_opacity(
                        0.10,
                        AppColors.WARNING if alert_count else ft.Colors.ON_SURFACE,
                    ),
                ),
                ft.Text(
                    kp_text,
                    size=tokens.FONT_XS,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                    style=AppColors.data_text_style(size=tokens.FONT_XS),
                ),
                ft.Container(expand=True),
                ft.OutlinedButton(
                    content=ft.Row(
                        [
                            ft.Text(
                                "Search or command…",
                                size=tokens.FONT_XS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Text(
                                "Ctrl K",
                                size=tokens.FONT_XXS,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                        spacing=tokens.SPACE_SM,
                        tight=True,
                    ),
                    on_click=lambda _: on_command_palette(),
                ),
                ft.Row(actions, spacing=0),
            ],
            spacing=tokens.SPACE_MD,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.Padding(
            tokens.SPACE_MD, tokens.SPACE_SM, tokens.SPACE_MD, tokens.SPACE_SM
        ),
        border=ft.Border(bottom=ft.BorderSide(1, AppColors.get_border())),
        bgcolor=AppColors.get_surface(),
    )
