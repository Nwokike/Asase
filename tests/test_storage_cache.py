"""Tests for L1 Memory LRU & L2 Disk MsgPack/Gzip Telemetry Cache in StorageService."""

import gzip
import hashlib
import json
import time
from unittest.mock import MagicMock

import pytest

from services.storage_service import StorageService, get_cache_dir


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
async def test_storage_l2_msgpack_disk_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    page = MagicMock()
    page.session_id = None
    service = StorageService(page)

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
    page = MagicMock()
    page.session_id = None
    service = StorageService(page)

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
    page = MagicMock()
    page.session_id = None
    service = StorageService(page)

    key = "telemetry_expired"
    payload = {"data": "expired"}

    # Set TTL that expires instantly
    await service.set_cached_telemetry(key, payload, ttl_seconds=-10.0)
    cached = await service.get_cached_telemetry(key)
    assert cached is None
