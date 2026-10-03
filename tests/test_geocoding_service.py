"""Deep testing of Open-Meteo Geocoding & Elevation Services."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from conftest import mock_pool_response, mock_pool_side_effect
from flet_geolocator import GeolocatorPermissionStatus

from core.device_services import DeviceServices
from services import geocoding_service
from services.geocoding_service import GeocodingService


@pytest.mark.asyncio
async def test_geocoding_search_cities_success():
    mock_data = {
        "results": [
            {
                "name": "Accra",
                "country": "Ghana",
                "country_code": "GH",
                "admin1": "Greater Accra",
                "latitude": 5.556,
                "longitude": -0.1969,
                "elevation": 61.0,
                "population": 2291352,
            }
        ]
    }
    mock_resp = httpx.Response(
        200,
        json=mock_data,
        request=httpx.Request("GET", "https://geocoding-api.open-meteo.com"),
    )
    with mock_pool_response("services.geocoding_service", mock_resp):
        results = await GeocodingService.search_cities("Accra")
        assert len(results) == 1
        assert results[0]["name"] == "Accra"
        assert results[0]["country"] == "Ghana"
        assert results[0]["latitude"] == 5.556


@pytest.mark.asyncio
async def test_geocoding_short_query_noop():
    # Queries with < 2 characters return empty list without hitting network
    results = await GeocodingService.search_cities("A")
    assert results == []
    results_empty = await GeocodingService.search_cities("")
    assert results_empty == []


@pytest.mark.asyncio
async def test_elevation_lookup():
    mock_data = {"elevation": [128.0]}
    mock_resp = httpx.Response(
        200,
        json=mock_data,
        request=httpx.Request("GET", "https://api.open-meteo.com/v1/elevation"),
    )
    with mock_pool_response("services.geocoding_service", mock_resp):
        elev = await GeocodingService.get_elevation(6.5, 3.3)
        assert elev == 128.0


@pytest.mark.asyncio
async def test_elevation_fallback():
    with mock_pool_response(
        "services.geocoding_service", exc=httpx.ConnectTimeout("Timeout")
    ):
        elev = await GeocodingService.get_elevation(6.5, 3.3)
        assert elev is None  # failure distinct from genuine sea level (0.0)


@pytest.mark.asyncio
async def test_reverse_geocode_open_meteo_success():
    mock_data = {
        "results": [
            {
                "name": "Enugu",
                "country": "Nigeria",
                "country_code": "NG",
                "admin1": "Enugu State",
                "latitude": 6.441,
                "longitude": 7.498,
                "elevation": 220.0,
            }
        ]
    }
    mock_resp = httpx.Response(
        200,
        json=mock_data,
        request=httpx.Request("GET", "https://geocoding-api.open-meteo.com/v1/reverse"),
    )
    with mock_pool_response("services.geocoding_service", mock_resp):
        res = await GeocodingService.reverse_geocode(6.441, 7.498)
        assert res is not None
        assert res["name"] == "Enugu"
        assert res["country"] == "Nigeria"
        assert res["country_code"] == "NG"


@pytest.mark.asyncio
async def test_reverse_geocode_bigdatacloud_fallback():
    # Open-Meteo returns empty results -> falls back to BigDataCloud
    def _mock_get(url, **kwargs):
        if "open-meteo" in str(url):
            return httpx.Response(
                200, json={"results": []}, request=httpx.Request("GET", str(url))
            )
        if "bigdatacloud" in str(url):
            return httpx.Response(
                200,
                json={
                    "city": "Awka",
                    "countryName": "Nigeria",
                    "countryCode": "NG",
                    "principalSubdivision": "Anambra",
                },
                request=httpx.Request("GET", str(url)),
            )
        return httpx.Response(404, request=httpx.Request("GET", str(url)))

    with mock_pool_response("services.geocoding_service", exc=_mock_get):
        res = await GeocodingService.reverse_geocode(6.21, 7.07)
        assert res is not None
        assert res["name"] == "Awka"
        assert res["country"] == "Nigeria"


@pytest.mark.asyncio
async def test_geolocator_success_without_ip_estimates():
    # Real device geolocation resolves + reverse geocodes to a real city
    page = MagicMock()
    page.web = False
    success_args = []

    async def _on_success(lat, lon, name, country):
        success_args.append((lat, lon, name, country))

    import time
    from types import SimpleNamespace

    geo = MagicMock()
    geo.is_location_service_enabled = AsyncMock(return_value=True)
    geo.get_permission_status = AsyncMock(
        return_value=GeolocatorPermissionStatus.ALWAYS
    )
    # Realistic position shape: the freshness gate inspects accuracy /
    # timestamp, so a bare MagicMock (whose auto-attrs coerce to junk)
    # would be rejected. Real GeolocatorPosition uses Optional floats.
    geo.get_current_position = AsyncMock(
        return_value=SimpleNamespace(
            latitude=6.44,
            longitude=7.50,
            accuracy=50.0,
            timestamp=time.time() * 1000.0,
        )
    )
    geo.get_last_known_position = AsyncMock(return_value=None)

    with patch.object(
        GeocodingService,
        "reverse_geocode",
        new=AsyncMock(
            return_value={"name": "Enugu", "country": "Nigeria", "admin1": "Enugu"}
        ),
    ):
        await DeviceServices.locate_user(geo, page, _on_success, silent=True)

    assert success_args == [(6.44, 7.50, "Enugu", "Nigeria")]


@pytest.mark.asyncio
async def test_locate_user_gps_failure_stays_silent():
    # GPS-only policy: when geolocation fails, nothing is called — no IP
    # estimate ever guesses a city the user isn't in.
    page = MagicMock()
    page.web = False
    success_args = []

    async def _on_success(lat, lon, name, country):
        success_args.append((lat, lon, name, country))

    geo = MagicMock()
    geo.is_location_service_enabled = AsyncMock(return_value=True)
    geo.get_permission_status = AsyncMock(
        return_value=GeolocatorPermissionStatus.ALWAYS
    )

    async def _fail(**kwargs):
        raise RuntimeError("gps error")

    geo.get_current_position = MagicMock(side_effect=_fail)
    geo.get_last_known_position = AsyncMock(return_value=None)

    with patch.object(
        GeocodingService, "reverse_geocode", new=AsyncMock(return_value=None)
    ):
        await DeviceServices.locate_user(geo, page, _on_success, silent=True)

    assert success_args == []


@pytest.mark.asyncio
async def test_locate_user_web_uses_longer_timeout():
    # Web permission dialogs need more time — 15s vs 8s native.
    page = MagicMock()
    page.web = True
    geo = MagicMock()
    geo.is_location_service_enabled = AsyncMock(return_value=True)
    geo.get_permission_status = AsyncMock(
        return_value=GeolocatorPermissionStatus.ALWAYS
    )
    geo.get_current_position = AsyncMock(return_value=None)
    geo.get_last_known_position = AsyncMock(return_value=None)

    captured: dict = {}

    async def _capture_wait_for(coro, timeout=None):
        captured["timeout"] = timeout
        coro.close()
        raise TimeoutError

    with (
        patch.object(
            GeocodingService, "reverse_geocode", new=AsyncMock(return_value=None)
        ),
        patch("asyncio.wait_for", new=_capture_wait_for),
    ):
        await DeviceServices.locate_user(geo, page, lambda *a: None, silent=True)

    assert captured["timeout"] == 15.0


@pytest.mark.asyncio
async def test_search_cities_passes_params_not_url_query():
    """M8: the query travels via httpx ``params=`` (properly encoded),
    never string-interpolated into the URL."""
    captured: dict = {}

    async def route(url, **kwargs):
        captured["url"] = str(url)
        captured["params"] = kwargs.get("params")
        return httpx.Response(
            200, json={"results": []}, request=httpx.Request("GET", str(url))
        )

    geocoding_service._GEOCODE_LRU.clear()
    try:
        with mock_pool_side_effect("services.geocoding_service", route):
            await GeocodingService.search_cities("New York")
    finally:
        geocoding_service._GEOCODE_LRU.clear()

    assert "?" not in captured["url"]
    assert captured["params"]["name"] == "new york"
    assert captured["params"]["count"] == 10
    assert captured["params"]["format"] == "json"


def _city_payload(query: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "results": [
                {
                    "name": query.title(),
                    "country": "Nigeria",
                    "country_code": "NG",
                    "admin1": "Kaduna",
                    "latitude": 10.52,
                    "longitude": 7.44,
                    "elevation": 600.0,
                    "population": 1000000,
                }
            ]
        },
        request=httpx.Request("GET", "https://geocoding-api.open-meteo.com"),
    )


@pytest.mark.asyncio
async def test_search_cities_cache_hit_skips_network():
    geocoding_service._GEOCODE_LRU.clear()
    calls = {"n": 0}

    async def route(url, **kwargs):
        calls["n"] += 1
        return _city_payload("Kaduna")

    try:
        with mock_pool_side_effect("services.geocoding_service", route):
            first = await GeocodingService.search_cities("Kaduna")
            second = await GeocodingService.search_cities("Kaduna")
        assert calls["n"] == 1  # second call served from the LRU
        assert second == first
    finally:
        geocoding_service._GEOCODE_LRU.clear()


@pytest.mark.asyncio
async def test_search_cities_cache_returns_defensive_copies():
    """Callers mutate result dicts in place — the cache must survive."""
    geocoding_service._GEOCODE_LRU.clear()

    async def route(url, **kwargs):
        return _city_payload("Kaduna")

    try:
        with mock_pool_side_effect("services.geocoding_service", route):
            first = await GeocodingService.search_cities("Kaduna")
            first[0]["name"] = "MUTATED"
            second = await GeocodingService.search_cities("Kaduna")
        assert second[0]["name"] == "Kaduna"
    finally:
        geocoding_service._GEOCODE_LRU.clear()


@pytest.mark.asyncio
async def test_reverse_geocode_cache_returns_defensive_copies():
    mock_data = {
        "results": [
            {
                "name": "Nsukka",
                "country": "Nigeria",
                "country_code": "NG",
                "admin1": "Enugu State",
                "latitude": 6.857,
                "longitude": 7.396,
                "elevation": 550.0,
            }
        ]
    }
    mock_resp = httpx.Response(
        200,
        json=mock_data,
        request=httpx.Request("GET", "https://geocoding-api.open-meteo.com/v1/reverse"),
    )
    geocoding_service._REVERSE_GEOCODE_LRU.clear()
    try:
        with mock_pool_response("services.geocoding_service", mock_resp):
            first = await GeocodingService.reverse_geocode(6.857, 7.396)
            first["name"] = "MUTATED"
            second = await GeocodingService.reverse_geocode(6.857, 7.396)
        assert second is not None
        assert second["name"] == "Nsukka"
    finally:
        geocoding_service._REVERSE_GEOCODE_LRU.clear()
