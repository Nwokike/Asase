"""Fail-open feed parsing: one poisoned record must not discard the batch.

Regression tests for the whole-collection model_validate_json data-loss
class (seismic, EONET, geocoding) plus the null-Kp crash.
"""

import httpx
import pytest
from conftest import mock_pool_response, mock_pool_side_effect

from services import geocoding_service
from services.atmospheric_service import AtmosphericService
from services.disaster_service import DisasterService
from services.geocoding_service import GeocodingService
from services.seismic_service import SeismicService
from services.space_weather_service import SpaceWeatherService


@pytest.fixture(autouse=True)
def _clear_geocode_caches():
    """The service-level LRU dicts persist across tests — isolate them."""
    geocoding_service._GEOCODE_LRU.clear()
    geocoding_service._REVERSE_GEOCODE_LRU.clear()
    yield
    geocoding_service._GEOCODE_LRU.clear()
    geocoding_service._REVERSE_GEOCODE_LRU.clear()


def _resp(payload, status=200):
    return httpx.Response(
        status,
        json=payload,
        request=httpx.Request("GET", "https://example.invalid"),
    )


_GOOD_FEATURE = {
    "id": "good",
    "properties": {"mag": 5.0, "title": "M5", "place": "X", "time": 1700000000000},
    "geometry": {"coordinates": [-115.0, 36.0, 5.0]},
}


@pytest.mark.asyncio
async def test_seismic_null_mag_feature_does_not_poison_batch():
    payload = {
        "features": [
            _GOOD_FEATURE,
            {
                "id": "bad",
                "properties": {
                    "mag": None,
                    "title": "M?",
                    "place": "Y",
                    "time": 1700000000000,
                },
                "geometry": {"coordinates": [-116.0, 37.0, 6.0]},
            },
        ]
    }
    with mock_pool_response("services.seismic_service", _resp(payload)):
        events = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
    assert [e["id"] for e in events] == ["good"]


@pytest.mark.asyncio
async def test_seismic_null_geometry_feature_skipped():
    payload = {
        "features": [
            {
                "id": "nogeom",
                "properties": {
                    "mag": 5.0,
                    "title": "M5",
                    "place": "X",
                    "time": 1700000000000,
                },
                "geometry": None,
            }
        ]
    }
    with mock_pool_response("services.seismic_service", _resp(payload)):
        events = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
    # Null-geometry events are dropped — their dict maps to (0,0), which
    # would otherwise paint a ghost marker at Null Island.
    assert events == []


@pytest.mark.asyncio
async def test_disaster_bad_event_does_not_poison_batch():
    payload = {
        "events": [
            {
                "id": "E1",
                "title": "Fire",
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "geometry": [{"date": "2026-08-30", "coordinates": [-120.0, 37.5]}],
            },
            {"id": None, "title": None},  # missing required shape
            {
                "id": "E3",
                "title": "Storm",
                "categories": [{"id": "severeStorms", "title": "Severe Storms"}],
                "geometry": [{"date": "2026-08-30", "coordinates": [[["oops"]]]}],
            },
        ]
    }
    with mock_pool_response("services.disaster_service", _resp(payload)):
        events = await DisasterService.fetch_active_disasters()
    ids = [e["id"] for e in events]
    assert "E1" in ids
    assert "E3" not in ids  # ragged coords fall back to (0,0) → filtered


@pytest.mark.asyncio
async def test_geocoding_null_strings_do_not_reject_response():
    payload = {
        "results": [
            {
                "name": "Lagos",
                "latitude": 6.5,
                "longitude": 3.3,
                "country": None,
                "admin1": None,
                "country_code": None,
                "timezone": None,
                "population": None,
                "elevation": None,
            }
        ]
    }
    with mock_pool_response("services.geocoding_service", _resp(payload)):
        out = await GeocodingService.search_cities("lagos")
    assert len(out) == 1
    assert out[0]["country"] == ""
    assert out[0]["population"] == 0


@pytest.mark.asyncio
async def test_space_weather_null_kp_does_not_crash_fetch():
    async def _fake_get(self, url, **kwargs):
        if "planetary_k_index" in url or "kp" in url.lower():
            return _resp([{"time_tag": "2026-01-01T00:00:00", "Kp": None}])
        return _resp(None, status=500)

    with mock_pool_side_effect("services.space_weather_service", _fake_get):
        data = await SpaceWeatherService.fetch_space_weather()
    assert data["kp_index"] == 0.0
    assert data["geomagnetic_status"] == "Quiet (Normal)"


@pytest.mark.asyncio
async def test_non_200_logs_and_returns_empty():
    # Real 503 path via the pooled seam (an earlier revision patched the
    # class-level AsyncClient.get with a sync return and only exercised
    # the swallowed await-TypeError branch).
    with mock_pool_response("core.network", _resp({"x": 1}, status=503)):
        assert await SeismicService.fetch_earthquakes() is None
        assert await DisasterService.fetch_active_disasters() is None
        assert await GeocodingService.search_cities("lagos") == []
        telemetry = await AtmosphericService.fetch_location_telemetry(6.5, 3.3)
        assert all(v == {} for v in telemetry.values())
