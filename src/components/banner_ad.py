"""BannerAd — single canonical banner ad builder (mobile only).

Sherlock/Proot pattern:
- Production unit ID only (no test IDs in the shipped tree).
- Pinned native 320x50 ad inside a glass card, centered full width.
- Pooled per slot: a fresh BannerAd per render throws away the live ad
  view and re-requests, flashing the slot — callers reuse one control
  per slot across re-renders.
- Consent is wired but never gates (owner's rule): the verdict is
  recorded, ads serve with or without it.

The mounted-but-unfilled AdView renders as an empty box on some devices
(Sherlock's field note) — the glass card makes that look deliberate
instead of like a rendering bug.
"""

from __future__ import annotations

import logging

import flet as ft
from flet import Control

from core.theme import adaptive_glass_bg, adaptive_glass_border

logger = logging.getLogger("asase.banner_ad")

# Production unit (AdMob console, Asase app ca-app-pub-5679949845754640~3484587388)
BANNER_ID_ANDROID = "ca-app-pub-5679949845754640/4500275250"

BANNER_WIDTH = 320
BANNER_HEIGHT = 50

_BANNER_POOL: dict[str, Control] = {}


def banner_unit_id() -> str:
    return BANNER_ID_ANDROID


def pooled_banner_ad(slot: str, page: ft.Page | None = None) -> Control:
    """Banner for `slot`, built once and reused across re-renders."""
    ad = _BANNER_POOL.get(slot)
    if ad is None:
        ad = build_banner_ad(page)
        _BANNER_POOL[slot] = ad
    return ad


def clear_banner_pool() -> None:
    """Drop every pooled banner (page teardown / theme change)."""
    _BANNER_POOL.clear()


def build_banner_ad(page: ft.Page | None = None) -> Control:
    """Glass-card-wrapped banner ad (mobile only).

    Desktop/web collapse to a zero-size container, so it is safe to place
    on shared screens.
    """
    if page is None:
        try:
            from flet import context

            page = context.page
        except Exception:
            return ft.Container(width=0, height=0)

    if not page or not hasattr(page, "platform"):
        return ft.Container(width=0, height=0)

    try:
        if not page.platform.is_mobile() or getattr(page, "web", False):
            return ft.Container(width=0, height=0)
    except Exception:
        return ft.Container(width=0, height=0)

    try:
        import flet_ads as fta

        ad = fta.BannerAd(
            unit_id=BANNER_ID_ANDROID,
            width=BANNER_WIDTH,
            height=BANNER_HEIGHT,
            on_load=lambda _e: logger.info("BannerAd loaded"),
            on_error=lambda e: logger.warning(
                "BannerAd load error: %s", getattr(e, "data", e)
            ),
        )
    except Exception as e:
        logger.warning("Failed to load BannerAd: %s", e)
        return ft.Container(width=0, height=0)

    banner = ft.Container(
        content=ft.Column(
            [
                ft.Container(
                    content=ad,
                    width=BANNER_WIDTH,
                    height=BANNER_HEIGHT,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            tight=True,
        ),
        expand=True,
        padding=ft.Padding(0, 8, 0, 8),
        border_radius=14,
        bgcolor=adaptive_glass_bg(page),
        border=ft.Border.all(1, adaptive_glass_border(page)),
    )
    return ft.Row(
        controls=[banner],
        alignment=ft.MainAxisAlignment.CENTER,
    )


# Aliases for flexible imports
AdMobBanner = build_banner_ad
BannerAd = build_banner_ad
