"""Safe notification dispatchers for Flet."""

from __future__ import annotations

import logging
import time

import flet as ft

from core.theme import AppColors

logger = logging.getLogger(__name__)

# Burst coalescing: identical messages within this window replace the
# in-flight toast instead of stacking (offline/online flaps, repeated
# refresh errors). Distinct messages always show.
_DEDUP_WINDOW_SEC = 2.0
_last_snack: tuple[str, str, float] | None = None


def reset_snack_dedup() -> None:
    """Test hook: clear the burst-coalescing memory."""
    global _last_snack
    _last_snack = None


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
    global _last_snack
    try:
        if page is None:
            logger.warning("show_snack dropped (no page): %s", message)
            return
        now = time.monotonic()
        if _last_snack is not None:
            last_message, last_bgcolor, last_at = _last_snack
            if (
                message == last_message
                and bgcolor == last_bgcolor
                and now - last_at < _DEDUP_WINDOW_SEC
            ):
                logger.debug("show_snack coalesced duplicate: %s", message)
                _last_snack = (message, bgcolor, now)
                return
        _last_snack = (message, bgcolor, now)
        snack = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=bgcolor,
            duration=duration,
        )
        page.show_dialog(snack)
    except Exception as ex:
        logger.warning("show_snack failed: %s", ex)
