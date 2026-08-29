"""Deep testing of Open-Meteo Atmospheric, AQI, and Flood Service."""

from unittest.mock import patch

import httpx
import pytest

from services.atmospheric_service import AtmosphericService


@pytest.mark.asyncio
async def test_atmospheric_success():
    weather_json = {
        "current": {
            "temperature_2m": 28.5,
            "apparent_temperature": 31.0,
            "relative_humidity_2m": 75,
            "surface_pressure": 1012.0,
            "wind_speed_10m": 12.0,
            "wind_gusts_10m": 25.0,
            "cape": 450,
            "uv_index": 7.5,
        }
    }
    aqi_json = {
        "current": {
            "us_aqi": 55,
            "pm2_5": 14.2,
            "pm10": 28.0,
            "carbon_monoxide": 210,
            "dust": 15,
        },
        "hourly": {
            "us_aqi": [40, 45, 50, 55],
        },
    }
    flood_json = {
        "daily": {
            "river_discharge": [120.5, 140.0, 160.2, 130.0],
        }
    }
    marine_json = {
        "current": {
            "wave_height": 1.8,
            "wave_period": 8.5,
            "swell_wave_height": 1.2,
        }
    }

    async def _mock_get(*args, **kwargs):
        url_str = ""
        for a in args:
            if isinstance(a, (str, httpx.URL)):
                url_str = str(a)
                break
        if not url_str and "url" in kwargs:
            url_str = str(kwargs["url"])

        if "air-quality" in url_str:
            return httpx.Response(
                200, json=aqi_json, request=httpx.Request("GET", url_str)
            )
        elif "/forecast" in url_str:
            return httpx.Response(
                200, json=weather_json, request=httpx.Request("GET", url_str)
            )
        elif "/flood" in url_str:
            return httpx.Response(
                200, json=flood_json, request=httpx.Request("GET", url_str)
            )
        elif "/marine" in url_str:
            return httpx.Response(
                200, json=marine_json, request=httpx.Request("GET", url_str)
            )
        return httpx.Response(
            404, request=httpx.Request("GET", url_str or "https://api.open-meteo.com")
        )

    with patch.object(httpx.AsyncClient, "get", side_effect=_mock_get):
        telemetry = await AtmosphericService.fetch_location_telemetry(6.5, 3.3)
        assert telemetry["weather"]["current"]["temperature_2m"] == 28.5
        assert telemetry["air_quality"]["current"]["us_aqi"] == 55
        assert telemetry["flood"]["daily"]["river_discharge"][0] == 120.5
        assert telemetry["marine"]["current"]["wave_height"] == 1.8


@pytest.mark.asyncio
async def test_atmospheric_partial_failures():
    async def _mock_get_error(*args, **kwargs):
        url_str = str(args[1]) if len(args) > 1 else str(args[0])
        if "marine" in url_str:
            return httpx.Response(
                400, text="Location not on ocean", request=httpx.Request("GET", url_str)
            )
        raise httpx.ReadTimeout("Timeout")

    with patch.object(httpx.AsyncClient, "get", side_effect=_mock_get_error):
        telemetry = await AtmosphericService.fetch_location_telemetry(51.5, -0.1)
        assert telemetry["weather"] == {}
        assert telemetry["air_quality"] == {}
        assert telemetry["flood"] == {}
        assert telemetry["marine"] == {}
