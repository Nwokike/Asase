"""Tests for L1 Memory LRU & L2 Disk MsgPack/Gzip Telemetry Cache in StorageService."""

import gzip
import hashlib
import json
import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.storage_service import StorageService, get_cache_dir


def _native_page():
    """A page in native mode — disk JSON + MsgPack cache."""
    page = MagicMock()
    page.web = False
    page.services = []
    return page


def _web_page():
    """A page in web mode — SharedPreferences-backed, no disk cache."""
    page = MagicMock()
    page.web = True
    page.services = []
    prefs = MagicMock()
    prefs._store: dict[str, str] = {}
    prefs.get = AsyncMock(side_effect=lambda k: prefs._store.get(k))
    prefs.set = AsyncMock(side_effect=lambda k, v: prefs._store.__setitem__(k, v))
    page._prefs = prefs
    return page, prefs


@pytest.mark.asyncio
async def test_storage_l1_memory_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    service = StorageService(_native_page())

    key = "telemetry_test_1"
    payload = {"weather": {"temp": 24.5}, "aqi": 35}

    await service.set_cached_telemetry(key, payload, ttl_seconds=60.0)
    cached = await service.get_cached_telemetry(key)
    assert cached == payload


@pytest.mark.asyncio
async def test_storage_l2_msgpack_disk_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    service = StorageService(_native_page())

    key = "telemetry_test_msgpack"
    payload = {"seismic_count": 12, "solar_kp": 3.66}

    await service.set_cached_telemetry(key, payload, ttl_seconds=300.0)

    # Clear L1 memory to force reading from L2 MsgPack disk
    service._l1_cache.clear()

    cached_from_disk = await service.get_cached_telemetry(key)
    assert cached_from_disk == payload
    assert key in service._l1_cache  # Re-populated into L1


@pytest.mark.asyncio
async def test_storage_l2_legacy_gzip_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    service = StorageService(_native_page())

    key = "telemetry_legacy_gzip"
    payload = {"legacy_data": [1, 2, 3]}

    # Write a legacy .json.gz file directly on disk
    h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    legacy_file = get_cache_dir() / f"{h}.json.gz"
    envelope = {"key": key, "expires_at": time.time() + 300, "data": payload}
    legacy_file.write_bytes(gzip.compress(json.dumps(envelope).encode("utf-8"), 6))

    cached_legacy = await service.get_cached_telemetry(key)
    assert cached_legacy == payload


@pytest.mark.asyncio
async def test_storage_cache_expired_ttl(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    service = StorageService(_native_page())

    key = "telemetry_expired"
    payload = {"data": "expired"}

    # Set TTL that expires instantly
    await service.set_cached_telemetry(key, payload, ttl_seconds=-10.0)
    cached = await service.get_cached_telemetry(key)
    assert cached is None


@pytest.mark.asyncio
async def test_web_l2_persists_across_sessions():
    # Web cold reload: L1 is gone, but the SharedPreferences envelope survives.
    page, prefs = _web_page()
    service = StorageService(page)
    service._prefs = prefs  # inject fake (constructor made a real one)

    key = "telemetry_6.50_3.40"
    payload = {"weather": {"temp": 29.1}, "air_quality": {"us_aqi": 88}}

    await service.set_cached_telemetry(key, payload, ttl_seconds=300.0)
    assert prefs._store  # written through to SharedPreferences

    # Fresh session — empty L1, same underlying prefs store
    revived = StorageService(page)
    revived._prefs = prefs
    revived._l1_cache.clear()
    cached = await revived.get_cached_telemetry(key)
    assert cached == payload


@pytest.mark.asyncio
async def test_web_l2_expired_envelope_evicted():
    page, prefs = _web_page()
    service = StorageService(page)
    service._prefs = prefs

    key = "telemetry_9.00_7.40"
    await service.set_cached_telemetry(key, {"stale": True}, ttl_seconds=-10.0)

    assert await service.get_cached_telemetry(key) is None
    # Expired envelope is dropped from the store, not kept as dead weight
    store = json.loads(prefs._store[StorageService._WEB_CACHE_KEY])
    assert key not in store


@pytest.mark.asyncio
async def test_web_l2_lru_eviction_capped_at_8():
    page, prefs = _web_page()
    service = StorageService(page)
    service._prefs = prefs

    for i in range(12):
        key = f"telemetry_{i:.2f}_0.00"
        await service.set_cached_telemetry(key, {"i": i}, ttl_seconds=300.0)

    store = json.loads(prefs._store[StorageService._WEB_CACHE_KEY])
    assert len(store) <= StorageService._MAX_WEB_ENVELOPES
    # Oldest keys evicted, newest survive
    assert "telemetry_0.00_0.00" not in store
    assert "telemetry_11.00_0.00" in store


@pytest.mark.asyncio
async def test_web_settings_persist_through_shared_preferences():
    # flet 0.86 removed page.client_storage — web settings go through the
    # SharedPreferences service as one JSON string under asase_storage.
    page, prefs = _web_page()
    service = StorageService(page)
    service._prefs = prefs

    await service.set("asase.theme", "dark")
    await service.flush()  # force the debounced write through

    # New session over the same prefs → settings reload
    revived = StorageService(page)
    revived._prefs = prefs
    assert await revived.get("asase.theme") == "dark"
