"""Disaster category param."""

from unittest.mock import patch

import httpx
import pytest

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
    with patch.object(httpx.AsyncClient, "get", return_value=resp) as m:
        evs = await DisasterService.fetch_active_disasters("all")
        assert len(evs) == 1
        called = str(m.call_args[0][0])
        assert "category=" not in called


@pytest.mark.asyncio
async def test_fetch_wildfire_category():
    resp = httpx.Response(
        200, json=EONET, request=httpx.Request("GET", "https://eonet.gsfc.nasa.gov")
    )
    with patch.object(httpx.AsyncClient, "get", return_value=resp) as m:
        await DisasterService.fetch_active_disasters("wildfire")
        assert "wildfires" in str(m.call_args[0][0])


@pytest.mark.asyncio
async def test_fetch_network_failure():
    with patch.object(httpx.AsyncClient, "get", side_effect=httpx.ConnectError("down")):
        assert await DisasterService.fetch_active_disasters() == []
