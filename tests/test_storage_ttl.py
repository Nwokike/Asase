"""Storage TTL."""

import pytest

from services.storage_service import StorageService


@pytest.mark.asyncio
async def test_l1_ttl_expired_returns_none(mock_page):
    s = StorageService(mock_page)
    await s.set_cached_telemetry("k1", {"x": 1}, ttl_seconds=-1)
    # advance by setting already expired
    assert await s.get_cached_telemetry("k1") is None


@pytest.mark.asyncio
async def test_l1_cache_hit(mock_page):
    s = StorageService(mock_page)
    await s.set_cached_telemetry("k2", {"y": 2}, ttl_seconds=60)
    assert await s.get_cached_telemetry("k2") == {"y": 2}


@pytest.mark.asyncio
async def test_l1_lru_eviction(mock_page):
    s = StorageService(mock_page)
    s._max_l1_items = 2
    # Fill 2, then third evicts oldest (a)
    await s.set_cached_telemetry("a", 1, ttl_seconds=60)
    await s.set_cached_telemetry("b", 2, ttl_seconds=60)
    # Insert c -> evicts a (FIFO for equal size)
    await s.set_cached_telemetry("c", 3, ttl_seconds=60)
    assert "a" not in s._l1_cache
    assert await s.get_cached_telemetry("c") == 3
