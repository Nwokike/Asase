"""Banner Ad component for Asase."""

from __future__ import annotations

import logging

import flet as ft

from state.app_state import state

logger = logging.getLogger("asase.banner_ad")


def build_banner_ad(page: ft.Page | None = None) -> ft.Control:
    """Builds a safe, non-intrusive banner ad container delegating to AdService."""
    if hasattr(state, "ad_service") and state.ad_service:
        return state.ad_service.get_banner_ad()

    # Fallback to direct AdService instantiation if page provided
    if page and not getattr(page, "web", False):
        try:
            from services.ad_service import AdService

            return AdService(page).get_banner_ad()
        except Exception:
            pass

    return ft.Container(width=0, height=0)


# Aliases for flexible imports
AdMobBanner = build_banner_ad
BannerAd = build_banner_ad
