"""Deep testing of Open-Meteo Geocoding & Elevation Services."""

from unittest.mock import patch

import httpx
import pytest

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
