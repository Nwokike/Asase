"""Service integration through the real HTTP seam.

Every test patches the pooled ``NetworkManager.get_client`` — never
``httpx.AsyncClient.get`` — so pool wiring, conditional requests, parsing,
and fail-open paths are genuinely exercised.
"""

from unittest.mock import patch

import httpx
import pytest
from conftest import mock_pool_get

from services.ad_service import AdService
from services.ai_service import stream_briefing
from services.atmospheric_service import AtmosphericService
from services.disaster_service import DisasterService
from services.geocoding_service import GeocodingService
from services.seismic_service import SeismicService
from services.space_weather_service import SpaceWeatherService
from services.update_service import UpdateService


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
    with mock_pool_get("services.seismic_service", mock_geojson):
        events = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
    assert len(events) == 1
    assert events[0]["magnitude"] == 5.2
    assert events[0]["place"] == "10km S of Tokyo, Japan"
    assert events[0]["latitude"] == 35.6895
    assert events[0]["longitude"] == 139.6917


@pytest.mark.asyncio
async def test_seismic_service_uses_pool_not_fresh_client():
    with mock_pool_get("services.seismic_service", {"features": []}) as (client, _):
        await SeismicService.fetch_earthquakes()
    client.get.assert_called_once()


@pytest.mark.asyncio
async def test_space_weather_service_parse():
    mock_kp = [
        ["2026-08-29 10:00:00", 2.33],
        ["2026-08-29 11:00:00", 3.67],
    ]
    with mock_pool_get("services.space_weather_service", mock_kp):
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
    with mock_pool_get("services.disaster_service", mock_eonet):
        disasters = await DisasterService.fetch_active_disasters()
    assert len(disasters) == 1
    assert disasters[0]["title"] == "Wildfire Alert"
    assert disasters[0]["type"] == "wildfire"


@pytest.mark.asyncio
async def test_atmospheric_service_parse():
    from core import validators

    validators.clear_records()
    payload_weather = {"current": {"temperature_2m": 29.5, "cape": 100.0}}
    payload_aqi = {"current": {"us_aqi": 55, "pm2_5": 12.0}}
    payload_flood = {"daily": {"river_discharge": [120.5]}}
    payload_marine = {"current": {"wave_height": 1.8}}

    def _resp_for(url, **kwargs):
        url = str(url)
        if "air-quality" in url:
            body = payload_aqi
        elif "flood" in url:
            body = payload_flood
        elif "marine" in url:
            body = payload_marine
        else:
            body = payload_weather
        return httpx.Response(200, json=body, request=httpx.Request("GET", url))

    from unittest.mock import AsyncMock, MagicMock

    from core.network import NetworkManager

    client = MagicMock()
    client.get = AsyncMock(side_effect=_resp_for)
    with patch.object(NetworkManager, "get_client", return_value=client):
        telemetry = await AtmosphericService.fetch_location_telemetry(6.5, 3.3)
    assert telemetry["weather"]["current"]["temperature_2m"] == 29.5
    assert telemetry["air_quality"]["current"]["us_aqi"] == 55
    assert telemetry["flood"]["daily"]["river_discharge"][0] == 120.5
    assert telemetry["marine"]["current"]["wave_height"] == 1.8
    assert client.get.call_count == 4
    validators.clear_records()


@pytest.mark.asyncio
async def test_geocoding_service_parse():
    from services import geocoding_service

    geocoding_service._GEOCODE_LRU.clear()
    try:
        with mock_pool_get(
            "services.geocoding_service",
            {"results": [{"name": "Accra", "latitude": 5.556, "longitude": -0.1969}]},
        ):
            results = await GeocodingService.search_cities("Accra")
        assert len(results) == 1
        assert results[0]["name"] == "Accra"
    finally:
        geocoding_service._GEOCODE_LRU.clear()


@pytest.mark.asyncio
async def test_ai_service_uses_pool():
    import json as _json
    from unittest.mock import MagicMock

    from tests.test_ai_service import _FakeStreamContext

    chunks = [_json.dumps({"choices": [{"delta": {"content": "hi"}}]})]
    lines = [f"data: {c}" for c in chunks]
    with mock_pool_get("services.ai_service", None) as (client, _):
        client.stream = MagicMock(return_value=_FakeStreamContext(lines))
        result = await stream_briefing("brief me", lambda t: None)
    assert result.text == "hi"


@pytest.mark.asyncio
async def test_update_service_parse():
    from core.constants import APP_BUILD_NUMBER

    payload = {
        "version": "9.9.9",
        "build_number": APP_BUILD_NUMBER + 1,
        "type": "update",
        "title": "New",
    }
    with mock_pool_get("services.update_service", payload):
        info = await UpdateService().check_for_update()
    assert info is not None
    assert info["version"] == "9.9.9"


@pytest.mark.asyncio
async def test_ad_service_platform_gating(mock_page):
    # AdService is UI-gated (no HTTP of its own); assert platform gating only.
    mock_page.platform.is_mobile.return_value = False
    svc = AdService(mock_page)
    assert svc.get_banner_ad() is not None
