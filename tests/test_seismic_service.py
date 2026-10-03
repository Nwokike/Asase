"""Deep testing of USGS Seismic Hazards Service."""

import httpx
import pytest
from conftest import mock_pool_response

from services.seismic_service import SeismicService


@pytest.mark.asyncio
async def test_seismic_empty_response():
    mock_resp = httpx.Response(
        status_code=200,
        json={"features": []},
        request=httpx.Request("GET", "https://earthquake.usgs.gov"),
    )
    with mock_pool_response("services.seismic_service", mock_resp):
        events = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
        assert events == []  # 200 with no features = genuinely empty feed


@pytest.mark.asyncio
async def test_seismic_magnitude_filter():
    mock_resp = httpx.Response(
        status_code=200,
        json={
            "features": [
                {
                    "id": "eq1",
                    "properties": {
                        "mag": 1.5,
                        "title": "M1.5 Minor",
                        "place": "Nevada",
                        "time": 1700000000000,
                    },
                    "geometry": {"coordinates": [-115.0, 36.0, 5.0]},
                },
                {
                    "id": "eq2",
                    "properties": {
                        "mag": 4.8,
                        "title": "M4.8 Moderate",
                        "place": "Chile",
                        "time": 1700000000000,
                    },
                    "geometry": {"coordinates": [-70.0, -33.0, 35.0]},
                },
            ]
        },
        request=httpx.Request("GET", "https://earthquake.usgs.gov"),
    )
    with mock_pool_response("services.seismic_service", mock_resp):
        # Filter M >= 2.5
        events = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
        assert len(events) == 1
        assert events[0]["id"] == "eq2"
        assert events[0]["magnitude"] == 4.8


@pytest.mark.asyncio
async def test_seismic_network_failure():
    with mock_pool_response(
        "services.seismic_service", exc=httpx.ConnectError("Network Down")
    ):
        events = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
        assert events is None  # failure distinct from an empty feed


@pytest.mark.asyncio
async def test_seismic_corrupted_json():
    mock_resp = httpx.Response(
        status_code=500,
        text="Internal Server Error",
        request=httpx.Request("GET", "https://earthquake.usgs.gov"),
    )
    with mock_pool_response("services.seismic_service", mock_resp):
        events = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
        assert events is None  # HTTP 500 = failure, not empty
