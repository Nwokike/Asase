"""Tests for L1 Memory LRU & L2 Disk Gzip Telemetry Cache in StorageService."""

from unittest.mock import MagicMock

import pytest

from services.storage_service import StorageService


@pytest.mark.asyncio
async def test_storage_l1_memory_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    page = MagicMock()
    page.session_id = None
    service = StorageService(page)

    key = "telemetry_test_1"
    payload = {"weather": {"temp": 24.5}, "aqi": 35}

    await service.set_cached_telemetry(key, payload, ttl_seconds=60.0)
    cached = await service.get_cached_telemetry(key)
    assert cached == payload


@pytest.mark.asyncio
async def test_storage_l2_gzip_disk_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    page = MagicMock()
    page.session_id = None
    service = StorageService(page)

    key = "telemetry_test_gzip"
    payload = {"seismic_count": 12, "solar_kp": 3.66}

    await service.set_cached_telemetry(key, payload, ttl_seconds=300.0)

    # Clear L1 memory to force reading from L2 Gzip disk
    service._l1_cache.clear()

    cached_from_disk = await service.get_cached_telemetry(key)
    assert cached_from_disk == payload
    assert key in service._l1_cache  # Re-populated into L1


@pytest.mark.asyncio
async def test_storage_cache_expired_ttl(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    page = MagicMock()
    page.session_id = None
    service = StorageService(page)

    key = "telemetry_expired"
    payload = {"data": "expired"}

    # Set TTL that expires instantly
    await service.set_cached_telemetry(key, payload, ttl_seconds=-10.0)
    cached = await service.get_cached_telemetry(key)
    assert cached is None
