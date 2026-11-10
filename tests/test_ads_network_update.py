"""Ads lifecycle, network pool, and update-gate regressions.

- Interstitial eviction by identity + consent re-check at show time.
- close() releases consent manager + interstitial (main.py shutdown path).
- Retry tuple covers pool-saturation timeouts; HTTP/2 reaches the pool.
- Announcements pass the build gate; explicit nulls fall back.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from conftest import mock_pool_response

from core.network import NetworkManager, ResilientRetryTransport
from services.ad_service import AdService
from services.update_service import UpdateService


def _mobile_page():
    page = MagicMock()
    page.web = False
    page.platform.is_mobile.return_value = True
    page.services = []
    return page


@pytest.mark.asyncio
async def test_handle_close_evicts_shown_interstitial():
    page = _mobile_page()
    svc = AdService(page)
    shown = MagicMock()
    page.services.append(shown)
    svc.interstitial = shown
    # Isolate eviction: stub the re-preload (consent no longer gates it,
    # so the old _can_request_ads=False trick no longer blocks it).
    svc.preload_interstitial = AsyncMock()
    await svc._handle_close(None)
    assert svc.interstitial is None
    assert all(s is not shown for s in page.services)


@pytest.mark.asyncio
async def test_show_interstitial_serves_despite_revoked_consent():
    """Owner's rule (all his apps): consent is wired but never gates —
    a declined/revoked verdict still serves the ad. The re-check runs
    (verdict recorded), the show proceeds."""
    page = _mobile_page()
    svc = AdService(page)
    interstitial = MagicMock()
    interstitial.show = AsyncMock()
    svc.interstitial = interstitial
    svc._can_request_ads = True
    manager = MagicMock()
    manager.can_request_ads = AsyncMock(return_value=False)  # revoked
    svc._consent_manager = manager

    assert await svc.show_interstitial(min_interval_seconds=0) is True
    interstitial.show.assert_called_once()
    assert svc._can_request_ads is False  # verdict recorded, not obeyed


@pytest.mark.asyncio
async def test_close_releases_services():
    page = _mobile_page()
    svc = AdService(page)
    consent, inter = MagicMock(), MagicMock()
    page.services.extend([consent, inter])
    svc._consent_manager = consent
    svc.interstitial = inter
    await svc.close()
    assert svc._consent_manager is None
    assert svc.interstitial is None
    assert page.services == []


def test_retry_tuple_covers_pool_saturation():
    assert httpx.PoolTimeout in ResilientRetryTransport.RETRIABLE_EXCEPTIONS
    assert httpx.WriteTimeout in ResilientRetryTransport.RETRIABLE_EXCEPTIONS


def test_http2_reaches_transport_pool():
    NetworkManager._client = None
    try:
        client = NetworkManager.get_client()
        transport = client._transport
        assert isinstance(transport, ResilientRetryTransport)
        pool = getattr(transport, "_pool", None)
        import sys

        if sys.platform != "emscripten":
            assert pool is not None and getattr(pool, "_http2", False) is True
    finally:
        NetworkManager._client = None


def _update_resp(payload, status=200):
    return httpx.Response(
        status, json=payload, request=httpx.Request("GET", "https://example.invalid")
    )


@pytest.mark.asyncio
async def test_announcement_passes_same_build_gate():
    from core.constants import APP_BUILD_NUMBER

    payload = {
        "version": "9.9.9",
        "build_number": APP_BUILD_NUMBER,
        "type": "announcement",
        "title": "Hello",
    }
    with mock_pool_response("services.update_service", _update_resp(payload)):
        info = await UpdateService().check_for_update()
    assert info is not None
    assert info["type"] == "announcement"


@pytest.mark.asyncio
async def test_update_explicit_nulls_fall_back():
    from core.constants import APP_BUILD_NUMBER, APP_VERSION

    payload = {
        "version": None,
        "build_number": APP_BUILD_NUMBER + 1,
        "type": None,
        "title": None,
        "release_notes": None,
        "github_url": None,
    }
    with mock_pool_response("services.update_service", _update_resp(payload)):
        info = await UpdateService().check_for_update()
    assert info is not None
    assert info["version"] == APP_VERSION
    assert info["type"] == "update"
    assert info["release_notes"] == ""


@pytest.mark.asyncio
async def test_update_same_build_non_announcement_suppressed():
    from core.constants import APP_BUILD_NUMBER

    payload = {
        "version": "9.9.9",
        "build_number": APP_BUILD_NUMBER,
        "type": "update",
    }
    with mock_pool_response("services.update_service", _update_resp(payload)):
        assert await UpdateService().check_for_update() is None
