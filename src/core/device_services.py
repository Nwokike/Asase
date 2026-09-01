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
from services.geocoding_service import GeocodingService

logger = logging.getLogger("asase.device")


class DeviceServices:
    """Helper methods for interacting with native mobile/desktop hardware APIs."""

    @staticmethod
    async def locate_user(
        geolocator: Geolocator | None,
        page: ft.Page,
        on_success: Callable[[float, float, str, str], Any],
    ) -> None:
        """Locate user using native device GPS with universal IP fallback and reverse geocoding.

        Works across all platforms (Android, iOS, Web, Linux, Windows, macOS).
        If native GPS/Geolocator fails, is denied, or is unsupported, automatically
        falls back to IP geolocation. In all cases, coordinates are reverse-geocoded
        to a real city name and country instead of a generic 'My Location'.
        """
        lat: float | None = None
        lon: float | None = None
        resolved_name: str = ""
        resolved_country: str = ""

        # ── 1. Attempt Native Geolocator (Mobile / Web / Desktop with GeoClue) ──
        if geolocator:
            try:
                is_enabled = await geolocator.is_location_service_enabled()
                if is_enabled:
                    status = await geolocator.get_permission_status()
                    if status in (
                        GeolocatorPermissionStatus.DENIED,
                        GeolocatorPermissionStatus.UNABLE_TO_DETERMINE,
                    ):
                        with contextlib.suppress(Exception):
                            status = await geolocator.request_permission()

                    if status not in (
                        GeolocatorPermissionStatus.DENIED,
                        GeolocatorPermissionStatus.DENIED_FOREVER,
                    ):
                        logger.info("Requesting high-accuracy device GPS position...")
                        import asyncio as _aio

                        pos = None
                        try:
                            pos = await _aio.wait_for(
                                geolocator.get_current_position(), timeout=8.0
                            )
                        except Exception:
                            pos = None

                        if not pos:
                            with contextlib.suppress(Exception):
                                pos = await geolocator.get_last_known_position()

                        if pos:
                            lat = float(pos.latitude)
                            lon = float(pos.longitude)
                            logger.info("Native GPS resolved: (%s, %s)", lat, lon)
            except Exception as ex:
                logger.debug("Native geolocator attempt bypassed/failed: %s", ex)

        # ── 2. Universal IP Geolocation Fallback (Linux / Desktop / GPS Timeout) ──
        if lat is None or lon is None:
            logger.info("Attempting IP-based geolocation fallback...")
            try:
                ip_loc = await GeocodingService.locate_by_ip()
                if ip_loc:
                    lat, lon, resolved_name, resolved_country = ip_loc
                    logger.info(
                        "IP Geolocation succeeded: %s, %s (%s, %s)",
                        resolved_name,
                        resolved_country,
                        lat,
                        lon,
                    )
            except Exception as ex:
                logger.warning("IP geolocation fallback failed: %s", ex)

        # ── 3. Resolve Real City & Country via Reverse Geocoding ──
        if lat is not None and lon is not None:
            if not resolved_name or resolved_name == "My Location":
                try:
                    rev = await GeocodingService.reverse_geocode(lat, lon)
                    if rev and rev.get("name"):
                        resolved_name = rev["name"]
                        resolved_country = rev.get("country", "")
                except Exception as ex:
                    logger.debug("Reverse geocoding missed: %s", ex)

            final_name = resolved_name or f"Location ({lat:.2f}, {lon:.2f})"
            final_country = resolved_country or ""

            try:
                await on_success(lat, lon, final_name, final_country)
                show_snack(
                    page,
                    f"Located: {final_name}{f', {final_country}' if final_country else ''}",
                    bgcolor=AppColors.SUCCESS,
                )
                return
            except Exception as ex:
                logger.warning("Location success callback error: %s", ex)

        # ── 4. Final Failure Guidance ──
        show_snack(
            page,
            "Could not determine your location — search for a place instead.",
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
