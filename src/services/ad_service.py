"""AdMob service for Asase — Banner, Interstitial, and UMP GDPR Consent.

Platform-aware: Only active on mobile (Android/iOS).
Gracefully collapses to zero-height containers on Desktop and Web.
"""

from __future__ import annotations

import inspect
import logging
import os
import time
from collections.abc import Callable

import flet as ft

logger = logging.getLogger("asase.ads")

try:
    import flet_ads as fta

    _HAS_ADS = True
except ImportError:
    _HAS_ADS = False


def _use_test_ids() -> bool:
    """Production unit IDs by default (owner's rule across all his apps).

    Flip ``ASASE_AD_TEST_IDS=1`` only for a local diagnostic build: Google's
    test units are served to every device, so a filled test banner proves
    the pipeline. Never ship with True — the family CI quality gate fails
    the build if Google's test IDs appear anywhere.
    """
    return os.getenv("ASASE_AD_TEST_IDS", "0") == "1"


class AdService:
    """Manages AdMob lifecycle, UMP consent, banner and interstitial ads."""

    USE_TEST_IDS = _use_test_ids()

    BANNER_ID_ANDROID_TEST = "ca-app-pub-3940256099942544/9214589741"
    INTERSTITIAL_ID_ANDROID_TEST = "ca-app-pub-3940256099942544/1033173712"

    # Production units (AdMob console, Asase app ca-app-pub-5679949845754640~3484587388)
    BANNER_ID_ANDROID_PROD = "ca-app-pub-5679949845754640/4500275250"
    INTERSTITIAL_ID_ANDROID_PROD = "ca-app-pub-5679949845754640/1548689184"

    # Owner's rule (all his apps): at least 60s between interstitials.
    INTERSTITIAL_MIN_INTERVAL_SEC = 60.0

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

    def is_mobile(self) -> bool:
        """Public platform gate for UI elements that only make sense on mobile."""
        return self._is_mobile()

    # ── Consent Management (UMP) ──────────────────────────────────────────────

    async def gather_consent(self) -> None:
        """Run UMP consent flow. Only shows UI in regulated regions (EEA/UK).

        The verdict is recorded for logging/policy — never obeyed as an ad
        gate (owner's rule, all his apps): if a user declines consent, ads
        still serve. A failed UMP flow also defaults to allow.
        """
        if not _HAS_ADS or not self._is_mobile() or not self.page:
            self._can_request_ads = True
            return
        try:
            self._consent_manager = fta.ConsentManager()
            self.page.services.append(self._consent_manager)
            await self._consent_manager.request_consent_info_update()
            await self._consent_manager.load_and_show_consent_form_if_required()
            self._can_request_ads = await self._consent_manager.can_request_ads()
            logger.info(
                "AdService: consent status recorded (can_request_ads=%s) — ads serve regardless",
                self._can_request_ads,
            )
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
        """Return a banner ad control, or empty container on desktop/web.

        Consent never gates (owner's rule): the verdict is recorded, ads
        serve with or without it.
        """
        if not _HAS_ADS or not self._is_mobile():
            return ft.Container(width=0, height=0)
        try:
            req = fta.AdRequest(
                keywords=[
                    "earthquake",
                    "weather",
                    "wildfire",
                    "disaster",
                    "atmosphere",
                    "planetary",
                ]
            )
            ad = fta.BannerAd(
                unit_id=self.banner_id,
                request=req,
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
        """Pre-load an interstitial ad for subsequent display.

        Consent never gates (owner's rule): ads serve with or without it.
        """
        self._on_close = on_close
        if not _HAS_ADS or not self._is_mobile() or not self.page:
            return
        try:
            req = fta.AdRequest(
                keywords=[
                    "earthquake",
                    "weather",
                    "space",
                    "hydrology",
                    "intelligence",
                ]
            )
            self.interstitial = fta.InterstitialAd(
                unit_id=self.interstitial_id,
                request=req,
                on_load=lambda e: logger.debug("Interstitial ad preloaded"),
                on_error=lambda e: logger.debug("Interstitial ad load error: %s", e),
                on_close=self._handle_close,
            )
            # Register InterstitialAd as an active page service
            if self.interstitial not in self.page.services:
                self.page.services.append(self.interstitial)
        except Exception as e:
            logger.debug("Interstitial ad preload failed: %s", e)
            self.interstitial = None

    def _evict_interstitial(self) -> None:
        """Remove the current interstitial from page.services by identity.

        InterstitialAd instances are single-use; the shown one is dead
        weight afterwards. Identity (not ``in``) eviction: dataclass
        ``__eq__`` on fresh lambdas makes ``in``-dedup unreliable.
        """
        current, self.interstitial = self.interstitial, None
        if current is not None and self.page is not None:
            try:
                services = self.page.services
                self.page.services = [s for s in services if s is not current]
            except Exception as ex:
                logger.debug("Interstitial evict failed: %s", ex)

    async def close(self) -> None:
        """Release all ad services (consent manager + interstitial).

        Called from the app shutdown path in main.py.
        """
        self._evict_interstitial()
        manager, self._consent_manager = self._consent_manager, None
        if manager is not None and self.page is not None:
            try:
                services = self.page.services
                self.page.services = [s for s in services if s is not manager]
            except Exception as ex:
                logger.debug("Consent manager evict failed: %s", ex)

    async def _refresh_consent(self) -> None:
        """Re-query UMP before showing — consent may have been revoked via
        the privacy form after the preload."""
        if self._consent_manager is None:
            return
        try:
            self._can_request_ads = await self._consent_manager.can_request_ads()
        except Exception as ex:
            logger.debug("Consent re-check failed, keeping prior state: %s", ex)

    async def _handle_close(self, e) -> None:
        if self._on_close:
            try:
                if inspect.iscoroutinefunction(self._on_close):
                    await self._on_close()
                else:
                    self._on_close()
            except Exception as ex:
                logger.warning("Error in interstitial on_close callback: %s", ex)
        self._evict_interstitial()
        await self.preload_interstitial(on_close=self._on_close)

    async def show_interstitial(
        self, min_interval_seconds: float | None = None
    ) -> bool:
        """Show preloaded interstitial if cooldown interval has elapsed.

        Consent never gates (owner's rule): ads serve with or without it.
        """
        interval = (
            self.INTERSTITIAL_MIN_INTERVAL_SEC
            if min_interval_seconds is None
            else min_interval_seconds
        )
        now = time.time()
        if now - self._last_interstitial_time < interval:
            logger.debug(
                "Interstitial suppressed: cooldown active (%.1fs elapsed < %.1fs)",
                now - self._last_interstitial_time,
                interval,
            )
            return False

        await self._refresh_consent()
        if not self._is_mobile():
            return False
        if self.interstitial is not None:
            try:
                await self.interstitial.show()
                self._last_interstitial_time = now
                return True
            except Exception as e:
                logger.debug("Failed to display interstitial ad: %s", e)
                return False
        # Preloaded ad not ready (or already spent) — fall back to a fresh
        # self-loading instance that shows the moment the native side
        # finishes loading (Sherlock/Proot pattern).
        try:
            req = fta.AdRequest(
                keywords=["earthquake", "weather", "space", "intelligence"]
            )
            fresh = fta.InterstitialAd(
                unit_id=self.interstitial_id,
                request=req,
                on_load=lambda e: self.page.run_task(self._show_fresh, e),
                on_error=lambda e: logger.debug("Fresh interstitial load error: %s", e),
                on_close=self._handle_close,
            )
            if fresh not in self.page.services:
                self.page.services.append(fresh)
            self.interstitial = fresh
            self._last_interstitial_time = now
            return True
        except Exception as e:
            logger.debug("Fresh interstitial construction failed: %s", e)
            return False

    async def _show_fresh(self, e) -> None:
        try:
            await e.control.show()
        except Exception as ex:
            logger.debug("Fresh interstitial show failed: %s", ex)
