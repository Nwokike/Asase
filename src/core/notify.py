"""Safe notification dispatchers for Flet."""

from __future__ import annotations

import logging

import flet as ft

from core.theme import AppColors

logger = logging.getLogger(__name__)


def show_snack(
    page: ft.Page,
    message: str,
    bgcolor: str = AppColors.PRIMARY,
    duration: int = 4000,
) -> None:
    """Best-effort snackbar: logs failures, never raises.

    Flet 1.0.3's Page has no ``show_snack_bar`` (or ``open``) method — the
    only dialog entry points are ``show_dialog``/``pop_dialog``. ``SnackBar``
    subclasses ``DialogControl``, so ``show_dialog`` renders it correctly.
    """
    try:
        if page is None:
            logger.warning("show_snack dropped (no page): %s", message)
            return
        snack = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=bgcolor,
            duration=duration,
        )
        page.show_dialog(snack)
    except Exception as ex:
        logger.warning("show_snack failed: %s", ex)
