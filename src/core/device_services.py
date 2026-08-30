"""Device native integration services (GPS, Haptics, Share, URL Launcher)."""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Callable
from typing import Any

import flet as ft
from flet_geolocator import Geolocator, GeolocatorPermissionStatus

from core.notify import show_snack
from core.theme import AppColors

logger = logging.getLogger("asase.device")


class DeviceServices:
    """Helper methods for interacting with native mobile/desktop hardware APIs."""

    @staticmethod
    async def locate_user(
        geolocator: Geolocator | None,
        page: ft.Page,
        on_success: Callable[[float, float], Any],
    ) -> None:
        """Locate user using native device GPS with permission handling."""
        if not geolocator:
            return
        try:
            is_enabled = await geolocator.is_location_service_enabled()
            if not is_enabled:
                show_snack(
                    page,
                    "Location services aren't available on this device — search for a place instead.",
                    bgcolor=AppColors.WARNING,
                )
                return

            status = await geolocator.get_permission_status()
            if status in (
                GeolocatorPermissionStatus.DENIED,
                GeolocatorPermissionStatus.UNABLE_TO_DETERMINE,
            ):
                status = await geolocator.request_permission()

            if status in (
                GeolocatorPermissionStatus.DENIED,
                GeolocatorPermissionStatus.DENIED_FOREVER,
            ):
                show_snack(
                    page,
                    "GPS Location permission denied.",
                    bgcolor=AppColors.WARNING,
                )
                return

            logger.info("Requesting high-accuracy device GPS position...")
            try:
                import asyncio as _aio

                pos = await _aio.wait_for(
                    geolocator.get_current_position(), timeout=12.0
                )
            except Exception:
                pos = None
            if not pos:
                with contextlib.suppress(Exception):
                    pos = await geolocator.get_last_known_position()

            if pos:
                lat = float(pos.latitude)
                lon = float(pos.longitude)
                logger.info("GPS Fix successfully resolved: (%s, %s)", lat, lon)
                await on_success(lat, lon)
                show_snack(page, "GPS Location Updated", bgcolor=AppColors.SUCCESS)
            else:
                show_snack(
                    page, "Could not obtain GPS lock.", bgcolor=AppColors.WARNING
                )
        except Exception as ex:
            logger.warning("GPS Geolocation failed: %s", ex)
            show_snack(
                page,
                "Could not retrieve GPS location.",
                bgcolor=AppColors.WARNING,
            )

    @staticmethod
    async def share_text(
        share: ft.Share | None,
        page: ft.Page,
        text: str,
        subject: str = "Planetary Alert",
    ) -> None:
        """Share text or report using native OS Share sheet with clipboard fallback."""
        if share:
            try:
                await share.share_text(text, title=subject, subject=subject)
                return
            except Exception as ex:
                logger.warning("Native share failed: %s", ex)

        with contextlib.suppress(Exception):
            # Flet clipboard is on Page, not a standalone control
            if hasattr(page, "set_clipboard"):
                await page.set_clipboard(text)
            elif hasattr(page, "clipboard"):
                await page.clipboard.set(text)
            else:
                # Fallback: show snack so user knows to copy manually
                show_snack(page, text[:120], bgcolor=AppColors.SUCCESS)
                return
            show_snack(page, "Copied to clipboard!", bgcolor=AppColors.SUCCESS)

    @staticmethod
    async def launch_url(url_launcher: ft.UrlLauncher | None, url: str) -> None:
        """Launch web link in external browser or custom tab."""
        if url_launcher and url:
            try:
                await url_launcher.launch_url(url)
            except Exception as ex:
                logger.warning("UrlLauncher failed for %s: %s", url, ex)
