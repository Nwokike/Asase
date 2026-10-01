"""Device native integration services (GPS, Haptics, Share, URL Launcher)."""

from __future__ import annotations

import contextlib
import logging
from collections.abc import Callable
from typing import Any

import flet as ft
from flet_geolocator import (
    Geolocator,
    GeolocatorConfiguration,
    GeolocatorPermissionStatus,
    GeolocatorPositionAccuracy,
)

from core.notify import show_snack
from core.theme import AppColors
from services.geocoding_service import GeocodingService

logger = logging.getLogger("asase.device")

# City-level tracking needs ~100m, not GPS-grade: MEDIUM fixes faster
# indoors and burns less battery than the plugin default (BEST).
_CITY_FIX_CONFIG = GeolocatorConfiguration(
    accuracy=GeolocatorPositionAccuracy.MEDIUM,
)

# Fixes older than this are treated as stale and ignored.
_MAX_FIX_AGE_SEC = 300.0
# Fixes less precise than this are ignored for city tracking.
_MAX_FIX_ACCURACY_M = 5000.0


class DeviceServices:
    """Helper methods for interacting with native mobile/desktop hardware APIs."""

    _locate_in_flight: bool = False

    @staticmethod
    def _fix_is_fresh(pos, now: float) -> bool:
        """Accept only live-enough, precise-enough fixes for city tracking.

        Unknown metadata (None / unparseable) is accepted — the plugin
        declares accuracy/timestamp Optional, and absence of evidence is
        not evidence of staleness. Only KNOWN-stale or KNOWN-imprecise
        fixes are rejected. Coordinates are always strictly validated.
        """
        accuracy = getattr(pos, "accuracy", None)
        if accuracy is not None:
            try:
                if float(accuracy) > _MAX_FIX_ACCURACY_M:
                    logger.debug("Rejecting low-accuracy fix: %s m", accuracy)
                    return False
            except (TypeError, ValueError):
                pass
        timestamp = getattr(pos, "timestamp", None)
        if timestamp is not None:
            try:
                age = now - float(timestamp) / 1000.0
                if age > _MAX_FIX_AGE_SEC:
                    logger.debug("Rejecting stale fix: %.0fs old", age)
                    return False
            except (TypeError, ValueError):
                pass
        lat, lon = getattr(pos, "latitude", None), getattr(pos, "longitude", None)
        try:
            if lat is None or lon is None:
                return False
            float(lat)
            float(lon)
        except (TypeError, ValueError):
            return False
        return True

    @staticmethod
    async def locate_user(
        geolocator: Geolocator | None,
        page: ft.Page,
        on_success: Callable[[float, float, str, str], Any],
        silent: bool = False,
    ) -> None:
        """Locate user via real device geolocation only — no IP estimates.

        Works across all platforms (Android, iOS, Web, Linux, Windows, macOS):
        the geolocator plugin uses native GPS off-web and the browser
        Geolocation API on web. If geolocation is denied, unsupported, or
        times out, we stay unlocated (Global Telemetry) and guide the user to
        search — never guessing a city from an IP address. Coordinates are
        always reverse-geocoded to a real city name and country.
        """
        # One locate at a time — double-taps on the GPS button must not run
        # two permission requests / two reverse-geocode chains.
        if DeviceServices._locate_in_flight:
            logger.info("Locate already in progress — ignoring duplicate call")
            return
        DeviceServices._locate_in_flight = True
        try:
            await DeviceServices._locate_user_inner(
                geolocator, page, on_success, silent
            )
        finally:
            DeviceServices._locate_in_flight = False

    @staticmethod
    async def _locate_user_inner(
        geolocator: Geolocator | None,
        page: ft.Page,
        on_success: Callable[[float, float, str, str], Any],
        silent: bool = False,
    ) -> None:
        lat: float | None = None
        lon: float | None = None
        resolved_name: str = ""
        resolved_country: str = ""

        # Browser permission dialogs need time to answer; native GPS is faster.
        timeout = 15.0 if getattr(page, "web", False) else 8.0

        # ── 1. Native / Browser Geolocator ──
        is_web = getattr(page, "web", False) is True
        if geolocator:
            try:
                is_enabled = await geolocator.is_location_service_enabled()
                if not is_enabled:
                    # Distinct guidance: the radio is off, not the permission.
                    if not silent:
                        if not is_web:
                            try:
                                await geolocator.open_location_settings()
                            except Exception as ex:
                                logger.debug("open_location_settings failed: %s", ex)
                        show_snack(
                            page,
                            "Location services are off — enable GPS, or search for a place instead.",
                            bgcolor=AppColors.WARNING,
                        )
                    return
                status = await geolocator.get_permission_status()
                if status in (
                    GeolocatorPermissionStatus.DENIED,
                    GeolocatorPermissionStatus.UNABLE_TO_DETERMINE,
                ):
                    with contextlib.suppress(Exception):
                        status = await geolocator.request_permission()

                if status == GeolocatorPermissionStatus.DENIED_FOREVER:
                    # Dead end for requests — deep-link to app settings.
                    if not silent:
                        if not is_web:
                            try:
                                await geolocator.open_app_settings()
                            except Exception as ex:
                                logger.debug("open_app_settings failed: %s", ex)
                        show_snack(
                            page,
                            "Location permission is blocked — allow it in Settings, or search for a place instead.",
                            bgcolor=AppColors.WARNING,
                        )
                    return
                if status != GeolocatorPermissionStatus.DENIED:
                    logger.info("Requesting balanced-accuracy device position...")
                    import asyncio as _aio
                    import time as _time

                    pos = None
                    try:
                        pos = await _aio.wait_for(
                            geolocator.get_current_position(
                                configuration=_CITY_FIX_CONFIG
                            ),
                            timeout=timeout,
                        )
                    except Exception:
                        pos = None

                    if not pos and not is_web:
                        # get_last_known_position raises on web — the web
                        # Geolocation API has no cached-position concept.
                        with contextlib.suppress(Exception):
                            pos = await geolocator.get_last_known_position()
                    elif not pos:
                        logger.debug("Web locate: no cached-position fallback")

                    if pos and DeviceServices._fix_is_fresh(pos, _time.time()):
                        lat = float(pos.latitude)
                        lon = float(pos.longitude)
                        logger.info("Device position resolved: (%s, %s)", lat, lon)
            except Exception as ex:
                logger.debug("Native geolocator attempt bypassed/failed: %s", ex)

        # ── 2. Resolve Real City & Country via Reverse Geocoding ──
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

        # ── 3. Final Failure Guidance (only if user explicitly triggered locate) ──
        if not silent:
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
        clipboard: ft.Clipboard | None = None,
    ) -> None:
        """Share text or report using native OS Share sheet with clipboard fallback."""
        if share:
            try:
                await share.share_text(text, title=subject, subject=subject)
                return
            except Exception as ex:
                logger.warning("Native share failed: %s", ex)

        # Flet 1.0.3 exposes clipboard only via the ft.Clipboard service
        # (Page has no set_clipboard/clipboard attributes) — the caller
        # passes the controller-held mounted instance.
        if clipboard is not None:
            try:
                await clipboard.set(text)
                show_snack(page, "Copied to clipboard!", bgcolor=AppColors.SUCCESS)
                return
            except Exception as ex:
                logger.debug("Clipboard copy failed: %s", ex)
        show_snack(page, text[:120], bgcolor=AppColors.SUCCESS)

    @staticmethod
    async def launch_url(url_launcher: ft.UrlLauncher | None, url: str) -> None:
        """Launch web link in external browser or custom tab."""
        if url_launcher and url:
            try:
                await url_launcher.launch_url(url)
            except Exception as ex:
                logger.warning("UrlLauncher failed for %s: %s", url, ex)
