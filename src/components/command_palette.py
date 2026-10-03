"""Command-K palette: fuzzy search over actions, places, and events.

The status bar already renders a "Search or command… Ctrl K" button
(adaptive_nav.py:362-379) wired to a no-op. This module implements the
palette itself: a dialog with a text field, a filtered result list, and
keyboard navigation (arrows + enter).

Fuzzy matching is substring-based (case-insensitive) — no external
dependency, works offline, and is fast enough for the small index
(<100 items).
"""

from __future__ import annotations

import logging
from typing import Any

import flet as ft

from core import tokens
from core.theme import AppColors

logger = logging.getLogger("asase.palette")


def _fuzzy_match(query: str, text: str) -> bool:
    """Case-insensitive substring match."""
    return query.lower() in text.lower()


def build_palette_index(
    bookmarks: list[dict],
    recent_searches: list[dict],
    earthquakes: list[dict],
    disasters: list[dict],
) -> list[dict[str, Any]]:
    """Build the searchable index from current state.

    Each entry: {"type": "action"|"place"|"event", "label": str,
                 "sub": str, "callback": Callable | None}
    """
    index: list[dict[str, Any]] = []

    # Actions
    index.append(
        {
            "type": "action",
            "label": "Go to Radar",
            "sub": "Dashboard overview",
            "callback": None,  # wired by caller
        }
    )
    index.append(
        {
            "type": "action",
            "label": "Go to Full Map",
            "sub": "Planetary hazard radar",
            "callback": None,
        }
    )
    index.append(
        {
            "type": "action",
            "label": "Go to Space Weather",
            "sub": "NOAA SWPC telemetry",
            "callback": None,
        }
    )
    index.append(
        {
            "type": "action",
            "label": "Go to History",
            "sub": "Saved locations & recent searches",
            "callback": None,
        }
    )
    index.append(
        {
            "type": "action",
            "label": "Go to Settings",
            "sub": "Configuration & diagnostics",
            "callback": None,
        }
    )
    index.append(
        {
            "type": "action",
            "label": "Refresh All Feeds",
            "sub": "Sync live telemetry",
            "callback": None,
        }
    )
    index.append(
        {
            "type": "action",
            "label": "Toggle Theme",
            "sub": "Dark / Light / System",
            "callback": None,
        }
    )

    # Places (bookmarks + recent searches)
    for b in bookmarks[:10]:
        index.append(
            {
                "type": "place",
                "label": b.get("name", "Unknown"),
                "sub": f"Bookmark • {b.get('country', '')}",
                "callback": None,
            }
        )
    for r in recent_searches[:10]:
        index.append(
            {
                "type": "place",
                "label": r.get("name", "Unknown"),
                "sub": f"Recent search • {r.get('country', '')}",
                "callback": None,
            }
        )

    # Events (top hazards by severity)
    for eq in earthquakes[:5]:
        index.append(
            {
                "type": "event",
                "label": eq.get("place", "Earthquake"),
                "sub": f"M{eq.get('magnitude', 0):.1f} • {eq.get('time_str', '')}",
                "callback": None,
            }
        )
    for d in disasters[:5]:
        index.append(
            {
                "type": "event",
                "label": d.get("title", "Natural Event"),
                "sub": f"{d.get('type', 'unknown').title()} • {d.get('date', '')[:10]}",
                "callback": None,
            }
        )

    return index


def filter_palette(
    index: list[dict[str, Any]], query: str | None
) -> list[dict[str, Any]]:
    """Filter the index by fuzzy match on label + sub."""
    # TextField.on_change can hand us None before the first keystroke.
    if not query or not query.strip():
        return index
    return [
        item
        for item in index
        if _fuzzy_match(query, item["label"]) or _fuzzy_match(query, item["sub"])
    ]


def show_command_palette(page: ft.Page, controller=None) -> None:
    """Open the command palette dialog.

    ``controller`` is the ControllerMethodsCtx instance from the shell —
    passing it explicitly (rather than reading page.context) is the only
    reliable way to reach the navigation closures.
    """
    from core.state import state as app_state

    def _nav_radar():
        if controller and controller.go_home:
            controller.go_home()

    def _nav_map():
        if controller and controller.show_map:
            controller.show_map()

    def _nav_space():
        if controller and controller.show_space:
            controller.show_space()

    def _nav_history():
        if controller and controller.show_history:
            controller.show_history()

    def _nav_settings():
        if controller and controller.show_settings:
            controller.show_settings()

    def _refresh():
        if controller and controller.refresh_all:
            controller.refresh_all()

    def _toggle_theme():
        if controller and controller.set_theme_mode:
            controller.set_theme_mode(None)

    def _open_version():
        from components.version_dialog import show_version_dialog

        show_version_dialog(page)

    # Build index with wired callbacks
    index = build_palette_index(
        app_state.bookmarks,
        app_state.recent_searches,
        app_state.earthquakes,
        app_state.disasters,
    )
    # Wire action callbacks
    for item in index:
        if item["type"] != "action":
            continue
        label = item["label"]
        if "Radar" in label:
            item["callback"] = _nav_radar
        elif "Full Map" in label:
            item["callback"] = _nav_map
        elif "Space" in label:
            item["callback"] = _nav_space
        elif "History" in label:
            item["callback"] = _nav_history
        elif "Settings" in label:
            item["callback"] = _nav_settings
        elif "Refresh" in label:
            item["callback"] = _refresh
        elif "Theme" in label:
            item["callback"] = _toggle_theme
        elif "Version" in label or "What's New" in label:
            item["callback"] = _open_version

    query_field = ft.TextField(
        hint_text="Type a command or search…",
        autofocus=True,
        border_radius=tokens.RADIUS_MD,
        text_size=tokens.FONT_SM,
        on_change=lambda e: _update_results(e.control.value),
    )

    results_column = ft.Column(
        [],
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
    )

    selected_index = [0]  # mutable closure

    def _update_results(query: str):
        filtered = filter_palette(index, query)
        results_column.controls.clear()
        # Clamp selection to valid range after filtering
        if selected_index[0] >= len(filtered):
            selected_index[0] = 0
        for i, item in enumerate(filtered[:20]):
            is_selected = i == selected_index[0]
            results_column.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(
                                ft.Icons.NAVIGATE_NEXT_ROUNDED
                                if item["type"] == "action"
                                else ft.Icons.LOCATION_ON_ROUNDED
                                if item["type"] == "place"
                                else ft.Icons.WARNING_AMBER_ROUNDED,
                                size=tokens.ICON_XS,
                                color=AppColors.PRIMARY
                                if item["type"] == "action"
                                else AppColors.OCEAN
                                if item["type"] == "place"
                                else AppColors.WARNING,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        item["label"],
                                        size=tokens.FONT_SM,
                                        weight=ft.FontWeight.W_600,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                    ft.Text(
                                        item["sub"],
                                        size=tokens.FONT_XXS,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                                spacing=0,
                                expand=True,
                            ),
                        ],
                        spacing=tokens.SPACE_SM,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=ft.Padding(
                        tokens.SPACE_MD,
                        tokens.SPACE_SM,
                        tokens.SPACE_MD,
                        tokens.SPACE_SM,
                    ),
                    border_radius=tokens.RADIUS_SM,
                    bgcolor=ft.Colors.with_opacity(0.08, AppColors.PRIMARY)
                    if is_selected
                    else None,
                    ink=True,
                    on_click=lambda _, item=item: _run_item(item),
                )
            )
        try:
            page.update()
        except Exception:
            logger.exception("Suppressed exception")

    # Save the shell's Ctrl+K handler so it's restored when the palette
    # closes — otherwise the keyboard hook stays hijacked and Ctrl+K dies.
    _previous_keyboard = page.on_keyboard_event

    def _close():
        page.on_keyboard_event = _previous_keyboard
        page.pop_dialog()

    def _run_item(item: dict[str, Any]):
        if item["callback"]:
            item["callback"]()
        _close()

    def _on_key(e: ft.KeyboardEvent):
        if e.key == "Escape":
            _close()
        elif e.key == "ArrowDown":
            selected_index[0] = min(
                selected_index[0] + 1, len(results_column.controls) - 1
            )
            _update_results(query_field.value or "")
        elif e.key == "ArrowUp":
            selected_index[0] = max(selected_index[0] - 1, 0)
            _update_results(query_field.value or "")
        elif e.key == "Enter":
            filtered = filter_palette(index, query_field.value or "")
            if filtered:
                _run_item(filtered[selected_index[0]])

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(
            "Command Palette", size=tokens.FONT_MD, weight=ft.FontWeight.BOLD
        ),
        content=ft.Column(
            [
                query_field,
                ft.Container(height=tokens.SPACE_SM),
                ft.Container(
                    content=results_column,
                    height=300,
                ),
            ],
            spacing=0,
            tight=True,
        ),
        actions=[],
        on_dismiss=lambda _: setattr(page, "on_keyboard_event", _previous_keyboard),
    )

    # Wire keyboard handler
    page.on_keyboard_event = _on_key

    # Initial population
    _update_results("")

    page.show_dialog(dlg)
