"""History/bookmark safety + cache-aliasing.

Regression tests: corrupt coordinates never crash row building, and
mutating a returned cache object never corrupts the cache.
"""

from unittest.mock import patch

import httpx
import pytest

from components.home.bookmarks_section import _safe_coords
from screens.history_screen import parse_history_coords


def test_parse_history_coords_valid():
    assert parse_history_coords({"lat": 6.5, "lon": 3.3}) == (6.5, 3.3)
    assert parse_history_coords({"latitude": 6.5, "longitude": 3.3}) == (6.5, 3.3)


def test_parse_history_coords_corrupt_returns_none():
    assert parse_history_coords({"lat": None, "lon": None}) is None
    assert parse_history_coords({"lat": "abc", "lon": "def"}) is None
    assert parse_history_coords({}) is None
    assert parse_history_coords({"lat": "--", "lon": "--"}) is None


def test_safe_coords_bookmark_variants():
    assert _safe_coords({"latitude": 1.0, "longitude": 2.0}) == (1.0, 2.0)
    assert _safe_coords({"lat": 1.0, "lon": 2.0}) == (1.0, 2.0)
    assert _safe_coords({"latitude": None, "longitude": 2.0}) is None
    assert _safe_coords({}) is None


def _resp(payload, status=200):
    return httpx.Response(
        status, json=payload, request=httpx.Request("GET", "https://example.invalid")
    )


@pytest.mark.asyncio
async def test_geocode_cache_mutation_does_not_corrupt():
    from services import geocoding_service
    from services.geocoding_service import GeocodingService

    geocoding_service._GEOCODE_LRU.clear()
    payload = {
        "results": [
            {
                "name": "Lagos",
                "latitude": 6.5,
                "longitude": 3.3,
                "elevation": 10.0,
            }
        ]
    }
    with patch.object(httpx.AsyncClient, "get", return_value=_resp(payload)):
        first = await GeocodingService.search_cities("lagos")
        first.append({"name": "POISON"})
        first[0]["name"] = "POISON"
        second = await GeocodingService.search_cities("lagos")
    assert len(second) == 1
    assert second[0]["name"] == "Lagos"
    geocoding_service._GEOCODE_LRU.clear()


@pytest.mark.asyncio
async def test_reverse_cache_mutation_does_not_corrupt():
    from services import geocoding_service
    from services.geocoding_service import GeocodingService

    geocoding_service._REVERSE_GEOCODE_LRU.clear()
    payload = {"results": [{"name": "Lagos", "latitude": 6.5, "longitude": 3.3}]}
    with patch.object(httpx.AsyncClient, "get", return_value=_resp(payload)):
        first = await GeocodingService.reverse_geocode(6.5, 3.3)
        first["name"] = "POISON"
        second = await GeocodingService.reverse_geocode(6.5, 3.3)
    assert second["name"] == "Lagos"
    geocoding_service._REVERSE_GEOCODE_LRU.clear()


@pytest.mark.asyncio
async def test_storage_cache_mutation_does_not_corrupt(tmp_path):
    import os

    os.environ["FLET_APP_STORAGE_DATA"] = str(tmp_path)
    from unittest.mock import MagicMock

    from services.storage_service import StorageService

    svc = StorageService(MagicMock())
    svc._is_web = False
    await svc.set_cached_telemetry("k", {"a": [1, 2]})
    got = await svc.get_cached_telemetry("k")
    got["a"].append(999)
    got["b"] = "POISON"
    again = await svc.get_cached_telemetry("k")
    assert again == {"a": [1, 2]}
    del os.environ["FLET_APP_STORAGE_DATA"]
