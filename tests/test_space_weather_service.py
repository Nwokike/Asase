"""Deep testing of NOAA SWPC Space Weather Service."""

from unittest.mock import patch

import httpx
import pytest

from services.space_weather_service import SpaceWeatherService


@pytest.mark.asyncio
async def test_space_weather_storm_levels():
    # Test G1 - G5 levels
    levels = [
        (2.0, "Quiet (Normal)"),
        (4.5, "Unsettled / Active"),
        (5.3, "G1 Minor"),
        (6.7, "G2 Moderate"),
        (7.5, "G3 Strong"),
        (8.8, "G4/G5 Severe"),
    ]
    for kp, expected_text in levels:
        mock_kp = [["2026-08-29 00:00", kp]]
        mock_resp = httpx.Response(
            200,
            json=mock_kp,
            request=httpx.Request("GET", "https://services.swpc.noaa.gov"),
        )
        with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
            sw = await SpaceWeatherService.fetch_space_weather()
            assert sw["kp_index"] == kp
            assert expected_text in sw["geomagnetic_status"]


@pytest.mark.asyncio
async def test_space_weather_empty_payload():
    mock_resp = httpx.Response(
        200, json=[], request=httpx.Request("GET", "https://services.swpc.noaa.gov")
    )
    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
        sw = await SpaceWeatherService.fetch_space_weather()
        assert sw["kp_index"] == 0.0
        assert "Quiet" in sw["geomagnetic_status"]
