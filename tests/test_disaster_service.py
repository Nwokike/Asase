"""Deep testing of NASA EONET and Disaster Services."""

from unittest.mock import patch

import httpx
import pytest

from services.disaster_service import DisasterService


@pytest.mark.asyncio
async def test_disaster_multi_category_parsing():
    mock_eonet = {
        "events": [
            {
                "id": "EONET_1",
                "title": "California Wildfire",
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "geometry": [{"date": "2026-08-29", "coordinates": [-120.5, 38.2]}],
                "link": "https://eonet.gsfc.nasa.gov",
            },
            {
                "id": "EONET_2",
                "title": "Tropical Cyclone Alpha",
                "categories": [{"id": "severeStorms", "title": "Severe Storms"}],
                "geometry": [{"date": "2026-08-29", "coordinates": [130.0, 20.0]}],
                "link": "https://eonet.gsfc.nasa.gov",
            },
            {
                "id": "EONET_3",
                "title": "Etna Volcano Eruption",
                "categories": [{"id": "volcanoes", "title": "Volcanoes"}],
                "geometry": [{"date": "2026-08-29", "coordinates": [15.0, 37.7]}],
                "link": "https://eonet.gsfc.nasa.gov",
            },
        ]
    }
    mock_resp = httpx.Response(
        200,
        json=mock_eonet,
        request=httpx.Request("GET", "https://eonet.gsfc.nasa.gov"),
    )
    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
        disasters = await DisasterService.fetch_active_disasters()
        assert len(disasters) == 3
        assert disasters[0]["type"] == "wildfire"
        assert disasters[1]["type"] == "storm"
        assert disasters[2]["type"] in ("volcano", "disaster")


@pytest.mark.asyncio
async def test_disaster_malformed_coordinates():
    mock_eonet = {
        "events": [
            {
                "id": "EONET_INVALID",
                "title": "No Geometry Event",
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "geometry": [],
            }
        ]
    }
    mock_resp = httpx.Response(
        200,
        json=mock_eonet,
        request=httpx.Request("GET", "https://eonet.gsfc.nasa.gov"),
    )
    with patch.object(httpx.AsyncClient, "get", return_value=mock_resp):
        disasters = await DisasterService.fetch_active_disasters()
        assert disasters == []
