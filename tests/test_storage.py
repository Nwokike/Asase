"""Tests for StorageService."""

import pytest

from services.storage_service import StorageService


@pytest.mark.asyncio
async def test_storage_service_basic_ops(mock_page, tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    storage = StorageService(mock_page)

    await storage.set("test_key", "test_value")
    val = await storage.get("test_key")
    assert val == "test_value"

    await storage.set("num_key", 12345)
    val_num = await storage.get("num_key")
    assert val_num == 12345

    await storage.delete("test_key")
    deleted_val = await storage.get("test_key")
    assert deleted_val is None

    await storage.flush()
    # Reload from disk
    storage_reloaded = StorageService(mock_page)
    assert await storage_reloaded.get("num_key") == 12345


@pytest.mark.asyncio
async def test_storage_service_bookmarks(mock_page, tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    storage = StorageService(mock_page)

    b = [{"name": "Tokyo, Japan", "latitude": 35.6895, "longitude": 139.6917}]
    await storage.set("asase.bookmarks", b)
    saved = await storage.get("asase.bookmarks")
    assert len(saved) == 1
    assert saved[0]["name"] == "Tokyo, Japan"
