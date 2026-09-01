"""Deep testing of Open-Meteo Geocoding & Elevation Services."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.device_services import DeviceServices
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
    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
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
    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
        elev = await GeocodingService.get_elevation(6.5, 3.3)
        assert elev == 128.0


@pytest.mark.asyncio
async def test_elevation_fallback():
    with patch.object(
        httpx.AsyncClient, "get", side_effect=httpx.ConnectTimeout("Timeout")
    ):
        elev = await GeocodingService.get_elevation(6.5, 3.3)
        assert elev == 0.0


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
    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
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

    with patch.object(httpx.AsyncClient, "get", side_effect=_mock_get):
        res = await GeocodingService.reverse_geocode(6.21, 7.07)
        assert res is not None
        assert res["name"] == "Awka"
        assert res["country"] == "Nigeria"


@pytest.mark.asyncio
async def test_locate_by_ip_ipapi_success():
    mock_data = {
        "latitude": 6.5244,
        "longitude": 3.3792,
        "city": "Lagos",
        "country_name": "Nigeria",
    }
    mock_resp = httpx.Response(
        200, json=mock_data, request=httpx.Request("GET", "https://ipapi.co/json/")
    )
    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
        res = await GeocodingService.locate_by_ip()
        assert res == (6.5244, 3.3792, "Lagos", "Nigeria")


@pytest.mark.asyncio
async def test_locate_by_ip_ipapi_fallback_to_ip_api():
    def _mock_get(url, **kwargs):
        if "ipapi.co" in str(url):
            return httpx.Response(500, request=httpx.Request("GET", str(url)))
        if "ip-api.com" in str(url):
            return httpx.Response(
                200,
                json={
                    "status": "success",
                    "lat": 5.55,
                    "lon": -0.19,
                    "city": "Accra",
                    "country": "Ghana",
                },
                request=httpx.Request("GET", str(url)),
            )
        return httpx.Response(404, request=httpx.Request("GET", str(url)))

    with patch.object(httpx.AsyncClient, "get", side_effect=_mock_get):
        res = await GeocodingService.locate_by_ip()
        assert res == (5.55, -0.19, "Accra", "Ghana")


@pytest.mark.asyncio
async def test_device_services_locate_user_ip_fallback():
    # Native geolocator is None or disabled -> triggers IP fallback and on_success
    page = MagicMock()
    success_args = []

    async def _on_success(lat, lon, name, country):
        success_args.append((lat, lon, name, country))

    with patch.object(
        GeocodingService,
        "locate_by_ip",
        new=AsyncMock(return_value=(6.44, 7.50, "Enugu", "Nigeria")),
    ):
        await DeviceServices.locate_user(None, page, _on_success)

    assert len(success_args) == 1
    assert success_args[0] == (6.44, 7.50, "Enugu", "Nigeria")
