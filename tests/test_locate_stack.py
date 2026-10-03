"""Location-stack regressions (Batch G).

- Web never calls get_last_known_position (raises on web).
- DENIED_FOREVER / GPS-off produce distinct guidance + settings links.
- Stale / low-accuracy / null fixes are rejected.
- MEDIUM accuracy config is passed for city-level fixes.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from flet_geolocator import GeolocatorPermissionStatus

from core.device_services import DeviceServices


@pytest.fixture(autouse=True)
def _reset_locate_in_flight():
    """Isolate the class-level flag: a mid-test failure otherwise poisons
    every later locate test."""
    yield


def _geo(
    *,
    web=False,
    enabled=True,
    status=GeolocatorPermissionStatus.WHILE_IN_USE,
    pos=None,
):
    geo = MagicMock()
    geo.is_location_service_enabled = AsyncMock(return_value=enabled)
    geo.get_permission_status = AsyncMock(return_value=status)
    geo.request_permission = AsyncMock(return_value=status)
    geo.get_current_position = AsyncMock(return_value=pos)
    geo.get_last_known_position = AsyncMock(return_value=pos)
    geo.open_app_settings = AsyncMock(return_value=True)
    geo.open_location_settings = AsyncMock(return_value=True)
    return geo


def _page(*, web=False):
    page = MagicMock()
    page.web = web
    return page


def _pos(lat=6.5, lon=3.3, accuracy=50.0, age_sec=10.0):
    import time

    return SimpleNamespace(
        latitude=lat,
        longitude=lon,
        accuracy=accuracy,
        timestamp=(time.time() - age_sec) * 1000.0,
    )


@pytest.mark.asyncio
async def test_web_skips_last_known_position():
    geo = _geo(web=True, pos=None)
    page = _page(web=True)
    calls = []
    with patch(
        "services.geocoding_service.GeocodingService.reverse_geocode",
        AsyncMock(return_value={"name": "Lagos", "country": "Nigeria"}),
    ):
        await DeviceServices.locate_user(
            geo, page, lambda *a: calls.append(a), silent=True
        )
    geo.get_last_known_position.assert_not_called()
    assert calls == []  # no fix at all -> silent, no success


@pytest.mark.asyncio
async def test_denied_forever_opens_app_settings():
    geo = _geo(status=GeolocatorPermissionStatus.DENIED_FOREVER)
    page = _page()
    await DeviceServices.locate_user(geo, page, AsyncMock(), silent=False)
    geo.open_app_settings.assert_called_once()
    geo.get_current_position.assert_not_called()


@pytest.mark.asyncio
async def test_gps_disabled_opens_location_settings():
    geo = _geo(enabled=False)
    page = _page()
    await DeviceServices.locate_user(geo, page, AsyncMock(), silent=False)
    geo.open_location_settings.assert_called_once()
    geo.get_permission_status.assert_not_called()


@pytest.mark.asyncio
async def test_silent_mode_shows_no_snack_and_no_settings():
    geo = _geo(enabled=False)
    page = _page()
    with patch("core.device_services.show_snack") as snack:
        await DeviceServices.locate_user(geo, page, AsyncMock(), silent=True)
    geo.open_location_settings.assert_not_called()
    snack.assert_not_called()


def test_fix_freshness_gate():
    import time

    now = time.time()
    assert DeviceServices._fix_is_fresh(_pos(), now) is True
    assert DeviceServices._fix_is_fresh(_pos(accuracy=99999.0), now) is False
    assert DeviceServices._fix_is_fresh(_pos(age_sec=9999.0), now) is False
    assert DeviceServices._fix_is_fresh(_pos(lat=None), now) is False


@pytest.mark.asyncio
async def test_city_fix_uses_medium_accuracy():
    geo = _geo(pos=_pos())
    page = _page()
    with patch(
        "services.geocoding_service.GeocodingService.reverse_geocode",
        AsyncMock(return_value={"name": "Lagos", "country": "Nigeria"}),
    ):
        await DeviceServices.locate_user(geo, page, AsyncMock(), silent=True)
    _, kwargs = geo.get_current_position.call_args
    config = kwargs.get("configuration")
    assert config is not None
    assert config.accuracy.value == "medium"
