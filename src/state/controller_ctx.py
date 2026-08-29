"""Controller methods dataclass and React-style context."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import flet as ft


@dataclass
class ControllerMethods:
    # Telemetry actions
    refresh_all: Callable[..., Any] | None = None
    search_location: Callable[[str], Any] | None = None
    select_coordinates: Callable[[float, float, str, str], Any] | None = None
    locate_user: Callable[..., Any] | None = None
    toggle_bookmark: Callable[[dict], Any] | None = None
    save_setting: Callable[[str, Any], Any] | None = None

    # Navigation closures injected by AppShell
    go_home: Callable[..., Any] | None = None
    show_map: Callable[..., Any] | None = None
    show_report: Callable[..., Any] | None = None
    show_space: Callable[..., Any] | None = None
    show_bookmarks: Callable[..., Any] | None = None
    show_settings: Callable[..., Any] | None = None
    back: Callable[..., Any] | None = None


ControllerMethodsCtx = ft.create_context(ControllerMethods())
