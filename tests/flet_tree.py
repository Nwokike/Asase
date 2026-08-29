"""Shared tree-walking helpers for testing Flet controls."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import flet as ft


def walk(c: Any) -> Iterable[Any]:
    """Yield all controls in the tree depth-first."""
    yield c
    children = getattr(c, "controls", None) or []
    if isinstance(children, list):
        for ch in children:
            yield from walk(ch)
    content = getattr(c, "content", None)
    if content is not None:
        yield from walk(content)


def walk_buttons(root: Any) -> Iterable[Any]:
    """Yield every button-like control in the tree."""
    for c in walk(root):
        if isinstance(
            c,
            (ft.FilledButton, ft.OutlinedButton, ft.ElevatedButton, ft.TextButton),
        ):
            yield c


def walk_icons(root: Any) -> Iterable[Any]:
    """Yield every icon-bearing control in the tree."""
    for c in walk(root):
        if isinstance(c, ft.Icon) or (
            isinstance(c, ft.IconButton) and getattr(c, "icon", None)
        ):
            yield c


def walk_texts(root: Any) -> Iterable[Any]:
    """Yield every ft.Text in the tree."""
    for c in walk(root):
        if isinstance(c, ft.Text):
            yield c


def walk_containers(root: Any) -> Iterable[Any]:
    """Yield every ft.Container in the tree."""
    for c in walk(root):
        if isinstance(c, ft.Container):
            yield c
