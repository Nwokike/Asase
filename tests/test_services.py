"""Tests for telemetry services."""

from unittest.mock import patch

import httpx
import pytest

from services.disaster_service import DisasterService
from services.seismic_service import SeismicService
from services.space_weather_service import SpaceWeatherService


@pytest.mark.asyncio
async def test_seismic_service_parse():
    mock_geojson = {
        "features": [
            {
                "id": "us1000abc",
                "properties": {
                    "mag": 5.2,
                    "place": "10km S of Tokyo, Japan",
                    "time": 1700000000000,
                    "tsunami": 0,
                    "alert": "green",
                    "url": "https://earthquake.usgs.gov",
                },
                "geometry": {
                    "coordinates": [139.6917, 35.6895, 30.0],
                },
            }
        ]
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_geojson,
        request=httpx.Request("GET", "https://earthquake.usgs.gov"),
    )

    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
        events = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
        assert len(events) == 1
        assert events[0]["magnitude"] == 5.2
        assert events[0]["place"] == "10km S of Tokyo, Japan"
        assert events[0]["latitude"] == 35.6895
        assert events[0]["longitude"] == 139.6917


@pytest.mark.asyncio
async def test_space_weather_service_parse():
    mock_kp = [
        ["2026-08-29 10:00:00", 2.33],
        ["2026-08-29 11:00:00", 3.67],
    ]

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_kp,
        request=httpx.Request("GET", "https://services.swpc.noaa.gov"),
    )

    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
        sw = await SpaceWeatherService.fetch_space_weather()
        assert sw["kp_index"] == 3.67
        assert "Active" in sw["geomagnetic_status"]


@pytest.mark.asyncio
async def test_disaster_service_parse():
    mock_eonet = {
        "events": [
            {
                "id": "EONET_123",
                "title": "Wildfire Alert",
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "geometry": [{"date": "2026-08-29", "coordinates": [10.0, 20.0]}],
                "link": "https://eonet.gsfc.nasa.gov",
            }
        ]
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_eonet,
        request=httpx.Request("GET", "https://eonet.gsfc.nasa.gov"),
    )

    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
        disasters = await DisasterService.fetch_active_disasters()
        assert len(disasters) == 1
        assert disasters[0]["title"] == "Wildfire Alert"
        assert disasters[0]["type"] == "wildfire"
