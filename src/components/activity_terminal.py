"""In-memory live activity terminal modal for diagnostics and logs."""

from __future__ import annotations

import logging

import flet as ft

from core import tokens
from core.logger_handler import in_memory_log_handler
from core.notify import show_snack
from core.theme import AppColors

logger = logging.getLogger("asase.terminal")


def show_activity_terminal_dialog(page: ft.Page) -> None:
    """Renders the live activity terminal dialog with dark green logs and copy button."""
    logs_list = in_memory_log_handler.get_logs()
    logs_str = (
        "\n".join(logs_list)
        if logs_list
        else "No planetary telemetry events recorded yet. Perform a search to stream live logs."
    )

    log_view = ft.Text(
        logs_str,
        font_family="Courier New",
        size=tokens.FONT_XS,
        color="#A6E22E",  # Terminal Monokai Green
        selectable=True,
    )

    async def _copy_logs(e=None):
        try:
            cb = ft.Clipboard()
            await cb.set(logs_str)
            show_snack(
                page, "Telemetry logs copied to clipboard!", bgcolor=AppColors.SUCCESS
            )
        except Exception as ex:
            logger.warning("Copy terminal logs failed: %s", ex)
            show_snack(
                page, "Failed to copy logs to clipboard.", bgcolor=AppColors.ERROR
            )

    dlg = ft.AlertDialog(
        title=ft.Row(
            [
                ft.Icon(
                    ft.Icons.TERMINAL_ROUNDED,
                    color=AppColors.PRIMARY,
                    size=tokens.ICON_MD,
                ),
                ft.Text(
                    "Planetary Activity Terminal",
                    font_family="Outfit",
                    size=tokens.FONT_LG,
                    weight=ft.FontWeight.BOLD,
                ),
            ],
            spacing=tokens.SPACE_SM,
        ),
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text(
                        "Live stream of all API requests, seismic feeds, and telemetry events.",
                        size=tokens.FONT_XS,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Container(
                        content=ft.Column([log_view], scroll=ft.ScrollMode.AUTO),
                        padding=tokens.SPACE_MD,
                        bgcolor="#0A0D14",
                        border=ft.Border.all(
                            1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)
                        ),
                        border_radius=tokens.RADIUS_MD,
                        expand=True,
                    ),
                ],
                spacing=tokens.SPACE_SM,
                expand=True,
            ),
            width=540,
            height=480,
        ),
        actions=[
            ft.IconButton(
                icon=ft.Icons.CONTENT_COPY_ROUNDED,
                tooltip="Copy Logs",
                on_click=lambda e: page.run_task(_copy_logs),
            ),
            ft.TextButton("Close", on_click=lambda e: page.pop_dialog()),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dlg)
