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
    share_text: Callable[[str, str], Coroutine[Any, Any, None]] | None = None
    launch_url: Callable[[str], Coroutine[Any, Any, None]] | None = None


ControllerMethodsCtx = ft.create_context(ControllerMethods())
