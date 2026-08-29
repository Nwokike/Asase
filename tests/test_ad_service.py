"""Tests for AdService initialization, platform routing, cooldown, and consent."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.ad_service import AdService


def test_ad_service_test_ids(mock_page):
    ad_svc = AdService(mock_page)
    ad_svc.USE_TEST_IDS = True

    assert ad_svc.banner_id == ad_svc.BANNER_ID_ANDROID_TEST
    assert ad_svc.interstitial_id == ad_svc.INTERSTITIAL_ID_ANDROID_TEST


def test_ad_service_prod_ids(mock_page):
    ad_svc = AdService(mock_page)
    ad_svc.USE_TEST_IDS = False

    assert ad_svc.banner_id == ad_svc.BANNER_ID_ANDROID_PROD
    assert ad_svc.interstitial_id == ad_svc.INTERSTITIAL_ID_ANDROID_PROD


def test_ad_service_desktop_graceful_banner(mock_page):
    mock_page.platform.is_mobile.return_value = False
    ad_svc = AdService(mock_page)
    banner = ad_svc.get_banner_ad()

    assert banner is not None
    assert getattr(banner, "width", None) == 0
    assert getattr(banner, "height", None) == 0


@pytest.mark.asyncio
async def test_ad_service_gather_consent_non_mobile(mock_page):
    mock_page.platform.is_mobile.return_value = False
    ad_svc = AdService(mock_page)

    await ad_svc.gather_consent()
    assert ad_svc._can_request_ads is True


@pytest.mark.asyncio
async def test_ad_service_interstitial_cooldown(mock_page):
    mock_page.platform.is_mobile.return_value = True
    ad_svc = AdService(mock_page)

    mock_interstitial = MagicMock()
    mock_interstitial.show = AsyncMock()
    ad_svc.interstitial = mock_interstitial

    # First show succeeds
    res1 = await ad_svc.show_interstitial(min_interval_seconds=60.0)
    assert res1 is True
    mock_interstitial.show.assert_called_once()

    # Immediate second show suppressed by cooldown
    res2 = await ad_svc.show_interstitial(min_interval_seconds=60.0)
    assert res2 is False


@pytest.mark.asyncio
async def test_ad_service_show_privacy_options_safe(mock_page):
    ad_svc = AdService(mock_page)
    # Should not raise even when _consent_manager is None
    await ad_svc.show_privacy_options()
