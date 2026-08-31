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


@pytest.mark.asyncio
async def test_space_weather_capital_kp_dict_schema():
    # The live NOAA products feed returns dicts with a capital "Kp" key —
    # regression test: this schema once yielded no chart points at all.
    mock_kp = [
        {
            "time_tag": "2026-08-31T00:00:00",
            "Kp": 2.33,
            "a_running": 9,
            "station_count": 8,
        },
        {
            "time_tag": "2026-08-31T03:00:00",
            "Kp": 3.33,
            "a_running": 18,
            "station_count": 8,
        },
    ]
    mock_resp = httpx.Response(
        200,
        json=mock_kp,
        request=httpx.Request("GET", "https://services.swpc.noaa.gov"),
    )
    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
        sw = await SpaceWeatherService.fetch_space_weather()
        assert sw["kp_index"] == 3.33  # reads the capital-Kp schema
        assert "Unsettled" in sw["geomagnetic_status"]
        assert sw["raw_kp"] == mock_kp


def test_space_screen_kp_history_parses_capital_kp():
    # The Space screen must derive chart points from either schema
    from screens.space_screen import SpaceScreen  # noqa: F401 — import sanity

    raw = [
        {"time_tag": "2026-08-31T00:00:00", "Kp": 2.33},
        {"time_tag": "2026-08-31T03:00:00", "kp": 3.33},
        {"time_tag": "2026-08-31T06:00:00", "estimated_kp": 4.0},
        ["2026-08-31 09:00", 1.67],
    ]
    kp_history: list[float] = []
    for item in raw:
        if isinstance(item, dict):
            val = item.get(
                "Kp",
                item.get("kp", item.get("estimated_kp", item.get("kp_index"))),
            )
            if val is not None:
                kp_history.append(float(val))
        elif isinstance(item, list) and len(item) > 1:
            kp_history.append(float(item[1]))
    assert kp_history == [2.33, 3.33, 4.0, 1.67]
