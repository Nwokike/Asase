"""Controller Methods Context for Asase React-style Component Tree."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

import flet as ft


@dataclass
class ControllerMethods:
    refresh_all: Callable[[], Coroutine[Any, Any, None]] | None = None
    select_coordinates: (
        Callable[[float, float, str, str], Coroutine[Any, Any, None]] | None
    ) = None
    locate_user: Callable[[], Coroutine[Any, Any, None]] | None = None
    save_setting: Callable[[str, Any], Coroutine[Any, Any, None]] | None = None
    toggle_bookmark: Callable[[dict], Coroutine[Any, Any, None]] | None = None
    show_map: Callable[[], None] | None = None
    show_space: Callable[[], None] | None = None
    show_report: Callable[[], None] | None = None
    show_settings: Callable[[], None] | None = None
    show_history: Callable[[], None] | None = None
    go_home: Callable[[], None] | None = None
    back: Callable[[], None] | None = None
    dismiss_onboarding: Callable[[], None] | None = None
    set_theme_mode: Callable[[ft.ThemeMode], None] | None = None
    open_report: Callable[[], Coroutine[Any, Any, None]] | None = None
    fetch_radius_history: (
        Callable[[float, float, float], Coroutine[Any, Any, list[dict]]] | None
    ) = None
    share_text: Callable[[str, str], Coroutine[Any, Any, None]] | None = None
    launch_url: Callable[[str], Coroutine[Any, Any, None]] | None = None
    navigate_tab: Callable[[int], None] | None = None


ControllerMethodsCtx = ft.create_context(ControllerMethods())
