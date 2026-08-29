"""AdMob service for Asase — Banner, Interstitial, and UMP GDPR Consent.

Platform-aware: Only active on mobile (Android/iOS).
Gracefully collapses to zero-height containers on Desktop and Web.
"""

from __future__ import annotations

import inspect
import logging
import time
from collections.abc import Callable

import flet as ft

logger = logging.getLogger("asase.ads")

try:
    import flet_ads as fta

    _HAS_ADS = True
except ImportError:
    _HAS_ADS = False


class AdService:
    """Manages AdMob lifecycle, UMP consent, banner and interstitial ads."""

    USE_TEST_IDS = False  # Production AdMob IDs active

    BANNER_ID_ANDROID_TEST = "ca-app-pub-3940256099942544/9214589741"
    INTERSTITIAL_ID_ANDROID_TEST = "ca-app-pub-3940256099942544/1033173712"

    BANNER_ID_ANDROID_PROD = "ca-app-pub-5679949845754640/6389274819"
    INTERSTITIAL_ID_ANDROID_PROD = "ca-app-pub-5679949845754640/5339329844"

    def __init__(self, page: ft.Page | None = None):
        self.page = page
        self.interstitial = None
        self._on_close: Callable | None = None
        self._can_request_ads: bool = True
        self._consent_manager = None
        self._last_interstitial_time: float = 0.0

    @property
    def banner_id(self) -> str:
        return (
            self.BANNER_ID_ANDROID_TEST
            if self.USE_TEST_IDS
            else self.BANNER_ID_ANDROID_PROD
        )

    @property
    def interstitial_id(self) -> str:
        return (
            self.INTERSTITIAL_ID_ANDROID_TEST
            if self.USE_TEST_IDS
            else self.INTERSTITIAL_ID_ANDROID_PROD
        )

    def _is_mobile(self) -> bool:
        if not self.page:
            return False
        try:
            is_web = getattr(self.page, "web", False) is True
            if is_web:
                return False
            platform = getattr(self.page, "platform", None)
            if platform and hasattr(platform, "is_mobile"):
                return bool(platform.is_mobile())
            return False
        except Exception:
            return False

    # ── Consent Management (UMP) ──────────────────────────────────────────────

    async def gather_consent(self) -> None:
        """Run UMP consent flow. Only shows UI in regulated regions (EEA/UK)."""
        if not _HAS_ADS or not self._is_mobile() or not self.page:
            self._can_request_ads = True
            return
        try:
            self._consent_manager = fta.ConsentManager()
            self.page.services.append(self._consent_manager)
            await self._consent_manager.request_consent_info_update()
            await self._consent_manager.load_and_show_consent_form_if_required()
            self._can_request_ads = await self._consent_manager.can_request_ads()
        except Exception as e:
            logger.warning("UMP consent flow failed, defaulting to allow ads: %s", e)
            self._can_request_ads = True

    async def show_privacy_options(self) -> None:
        """Show privacy options form if required by regulation (GDPR)."""
        if not self._consent_manager:
            return
        try:
            status = (
                await self._consent_manager.get_privacy_options_requirement_status()
            )
            if status == fta.PrivacyOptionsRequirementStatus.REQUIRED:
                await self._consent_manager.show_privacy_options_form()
                self._can_request_ads = await self._consent_manager.can_request_ads()
        except Exception as e:
            logger.debug("Failed to display privacy options: %s", e)

    # ── Ad Controls ───────────────────────────────────────────────────────────

    def get_banner_ad(self) -> ft.Control:
        """Return a banner ad control, or empty container on desktop/web."""
        if not _HAS_ADS or not self._is_mobile() or not self._can_request_ads:
            return ft.Container(width=0, height=0)
        try:
            ad = fta.BannerAd(
                unit_id=self.banner_id,
                size=fta.AdSize.BANNER,
                on_error=lambda e: logger.debug("Banner ad error: %s", e),
            )
            return ft.Container(
                content=ad,
                alignment=ft.Alignment.CENTER,
                padding=ft.Padding(0, 8, 0, 8),
            )
        except Exception as e:
            logger.debug("Banner ad initialization failed: %s", e)
            return ft.Container(width=0, height=0)

    async def preload_interstitial(self, on_close: Callable | None = None) -> None:
        """Pre-load an interstitial ad for subsequent display."""
        self._on_close = on_close
        if not _HAS_ADS or not self._is_mobile() or not self._can_request_ads:
            return
        try:
            self.interstitial = fta.InterstitialAd(
                unit_id=self.interstitial_id,
                on_load=lambda e: logger.debug("Interstitial ad preloaded"),
                on_error=lambda e: logger.debug("Interstitial ad load error: %s", e),
                on_close=self._handle_close,
            )
        except Exception as e:
            logger.debug("Interstitial ad preload failed: %s", e)
            self.interstitial = None

    async def _handle_close(self, e) -> None:
        if self._on_close:
            try:
                if inspect.iscoroutinefunction(self._on_close):
                    await self._on_close()
                else:
                    self._on_close()
            except Exception as ex:
                logger.warning("Error in interstitial on_close callback: %s", ex)
        await self.preload_interstitial(on_close=self._on_close)

    async def show_interstitial(self, min_interval_seconds: float = 90.0) -> bool:
        """Show preloaded interstitial if cooldown interval has elapsed."""
        now = time.time()
        if now - self._last_interstitial_time < min_interval_seconds:
            logger.debug(
                "Interstitial suppressed: cooldown active (%.1fs elapsed < %.1fs)",
                now - self._last_interstitial_time,
                min_interval_seconds,
            )
            return False

        if self.interstitial and self._is_mobile():
            try:
                await self.interstitial.show()
                self._last_interstitial_time = now
                return True
            except Exception as e:
                logger.debug("Failed to display interstitial ad: %s", e)
                return False
        return False
