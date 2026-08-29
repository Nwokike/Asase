"""Banner Ad component for Asase."""

from __future__ import annotations

import logging

import flet as ft

from core import tokens

logger = logging.getLogger("asase.banner_ad")
BANNER_AD_UNIT_ID = "ca-app-pub-5679949845754640/6389274819"


def build_banner_ad(page: ft.Page | None = None) -> ft.Control:
    """Builds a safe, non-intrusive banner ad container."""
    try:
        import flet_ads as ads

        ad = ads.BannerAd(
            unit_id=BANNER_AD_UNIT_ID,
            size=ads.AdSize.BANNER,
        )
        return ft.Container(
            content=ad,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding(0, tokens.SPACE_SM, 0, tokens.SPACE_SM),
        )
    except Exception as e:
        logger.debug("Banner ad unsupported: %s", e)
        return ft.Container(height=0)


# Aliases for flexible imports
AdMobBanner = build_banner_ad
BannerAd = build_banner_ad
