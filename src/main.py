"""Asase — Main Entry Point and App Bootstrapper."""

from __future__ import annotations

import contextlib
import logging

import flet as ft

from core.controller import AppController
from core.network import NetworkManager

logger = logging.getLogger("asase")


async def main(page: ft.Page) -> None:
    """Application entrypoint configuring logging, initializing controller, and managing lifecycle."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    controller = AppController(page)
    await controller.init()
    page.on_error = controller.on_error

    async def _on_close(e=None):
        controller.shutdown()
        with contextlib.suppress(Exception):
            if controller.storage:
                await controller.storage.flush()
        with contextlib.suppress(Exception):
            if controller.ad_service:
                await controller.ad_service.close()
        with contextlib.suppress(Exception):
            await NetworkManager.close()

    page.on_close = _on_close
    page.on_disconnect = _on_close


if __name__ == "__main__":
    ft.run(main, assets_dir="src/assets")
