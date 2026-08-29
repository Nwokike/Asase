"""Google AdMob Monetization service for Asase."""

from __future__ import annotations

import logging

import flet as ft

logger = logging.getLogger("asase.ads")

BANNER_AD_UNIT_ID = "ca-app-pub-5679949845754640/6389274819"
INTERSTITIAL_AD_UNIT_ID = "ca-app-pub-5679949845754640/9823412351"


class AdService:
    """Manages banner and interstitial ads across Android and fallback environments."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.interstitial = None
        self._is_mobile = getattr(page.platform, "is_mobile", lambda: False)()

    async def preload_interstitial(self) -> None:
        """Preloads interstitial ads on mobile platforms."""
        if not self._is_mobile:
            return
        try:
            # Dynamically imported so desktop/web run without errors
            import flet_ads as ads

            self.interstitial = ads.InterstitialAd(
                unit_id=INTERSTITIAL_AD_UNIT_ID,
                on_loaded=lambda _: logger.info("Interstitial ad loaded"),
                on_error=lambda e: logger.warning("Interstitial ad error: %s", e),
            )
            self.page.services.append(self.interstitial)
            await self.interstitial.load()
        except Exception as e:
            logger.debug("AdMob interstitial preload unavailable: %s", e)

    async def show_interstitial(self) -> None:
        """Shows the interstitial ad if ready."""
        if self.interstitial:
            try:
                await self.interstitial.show()
                await self.preload_interstitial()
            except Exception as e:
                logger.warning("Show interstitial failed: %s", e)

    async def close(self) -> None:
        pass
