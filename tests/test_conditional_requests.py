"""Conditional-request regressions (Batch O)."""

import httpx
import pytest
from conftest import mock_pool_response

from core import validators
from core.validators import conditional_get_json


def _resp(status, payload=None, headers=None):
    return httpx.Response(
        status,
        json=payload,
        headers=headers or {},
        request=httpx.Request("GET", "https://example.invalid"),
    )


@pytest.fixture(autouse=True)
def _clear_records():
    validators.clear_records()
    yield
    validators.clear_records()


@pytest.mark.asyncio
async def test_first_fetch_unconditional_then_304_short_circuits():
    body = {"features": []}
    first = _resp(200, body, {"etag": '"abc123"'})
    with mock_pool_response("core.validators", first):
        status, out = await conditional_get_json("https://x.test/feed")
    assert status == 200
    assert out == body
    # Validators stored; second call sends If-None-Match.
    assert validators._records["https://x.test/feed"]["etag"] == '"abc123"'

    second = _resp(304, None)
    with mock_pool_response("core.validators", second) as (client2, _m2):
        status2, out2 = await conditional_get_json("https://x.test/feed")
    assert status2 == 304
    assert out2 == body  # cached body, no re-parse needed
    sent_headers = client2.get.call_args.kwargs.get("headers", {})
    assert sent_headers.get("If-None-Match") == '"abc123"'


@pytest.mark.asyncio
async def test_seismic_uses_cached_304_body():
    from services.seismic_service import SeismicService

    good = {
        "features": [
            {
                "id": "eq1",
                "properties": {
                    "mag": 5.0,
                    "title": "M5",
                    "place": "X",
                    "time": 1700000000000,
                },
                "geometry": {"coordinates": [-115.0, 36.0, 5.0]},
            }
        ]
    }
    with mock_pool_response(
        "services.seismic_service", _resp(200, good, {"etag": '"e1"'})
    ):
        first = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
    assert len(first) == 1

    with mock_pool_response("services.seismic_service", _resp(304, None)):
        second = await SeismicService.fetch_earthquakes(min_magnitude=2.5)
    assert len(second) == 1
    assert second[0]["id"] == "eq1"


@pytest.mark.asyncio
async def test_disaster_uses_cached_304_body():
    from services.disaster_service import DisasterService

    payload = {
        "events": [
            {
                "id": "E1",
                "title": "Fire",
                "categories": [{"id": "wildfires", "title": "Wildfires"}],
                "geometry": [{"date": "2026-08-30", "coordinates": [-120.0, 37.5]}],
            }
        ]
    }
    with mock_pool_response(
        "services.disaster_service", _resp(200, payload, {"etag": '"e2"'})
    ):
        assert len(await DisasterService.fetch_active_disasters()) == 1
    with mock_pool_response("services.disaster_service", _resp(304, None)):
        assert len(await DisasterService.fetch_active_disasters()) == 1


@pytest.mark.asyncio
async def test_stale_validators_not_sent():
    import time

    validators._records["https://x.test/old"] = {
        "etag": '"stale"',
        "last_modified": None,
        "saved_at": time.time() - 7200.0,
        "body": {"x": 1},
    }
    with mock_pool_response("core.validators", _resp(200, {"x": 2})) as (client, _m):
        status, out = await conditional_get_json("https://x.test/old")
    assert status == 200
    assert out == {"x": 2}
    assert "headers" not in client.get.call_args.kwargs
