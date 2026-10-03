"""Disaster category param."""

import httpx
import pytest
from conftest import mock_pool_response

from services.disaster_service import DisasterService

EONET = {
    "title": "EONET",
    "events": [
        {
            "id": "E1",
            "title": "Fire",
            "link": "",
            "categories": [{"id": "wildfires", "title": "Wildfires"}],
            "geometry": [{"date": "2026-08-30", "coordinates": [-120.0, 37.5]}],
        }
    ],
}


@pytest.mark.asyncio
async def test_fetch_all():
    resp = httpx.Response(
        200, json=EONET, request=httpx.Request("GET", "https://eonet.gsfc.nasa.gov")
    )
    with mock_pool_response("services.disaster_service", resp) as (client, _m):
        evs = await DisasterService.fetch_active_disasters("all")
        assert len(evs) == 1
        called = str(client.get.call_args[0][0])
        assert "category=" not in called


@pytest.mark.asyncio
async def test_fetch_wildfire_category():
    resp = httpx.Response(
        200, json=EONET, request=httpx.Request("GET", "https://eonet.gsfc.nasa.gov")
    )
    with mock_pool_response("services.disaster_service", resp) as (client, _m):
        await DisasterService.fetch_active_disasters("wildfire")
        assert "wildfires" in str(client.get.call_args[0][0])


@pytest.mark.asyncio
async def test_fetch_network_failure():
    with mock_pool_response(
        "services.disaster_service", exc=httpx.ConnectError("down")
    ):
        assert await DisasterService.fetch_active_disasters() is None
