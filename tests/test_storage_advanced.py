"""Deep testing of StorageService resilience, atomic operations, and recovery."""

from pathlib import Path

import pytest

from services.storage_service import StorageService


@pytest.mark.asyncio
async def test_storage_corrupted_file_recovery(mock_page, tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    storage_dir = Path(tmp_path) / "asase"
    storage_dir.mkdir(parents=True, exist_ok=True)
    corrupted_file = storage_dir / "storage.json"
    corrupted_file.write_bytes(b"{invalid_json_bytes...")

    # Instantiating StorageService should detect corruption and backup to .json.corrupted
    storage = StorageService(mock_page)
    assert storage._data == {}
    assert (storage_dir / "storage.json.corrupted").exists()


@pytest.mark.asyncio
async def test_storage_backup_fallback(mock_page, tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    storage_dir = Path(tmp_path) / "asase"
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Corrupt main file, valid bak file
    (storage_dir / "storage.json").write_bytes(b"{bad json")
    (storage_dir / "storage.json.bak").write_bytes(
        b'{"recovered_key": "recovered_value"}'
    )

    storage = StorageService(mock_page)
    val = await storage.get("recovered_key")
    assert val == "recovered_value"


@pytest.mark.asyncio
async def test_storage_atomic_tmp_swap(mock_page, tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    storage = StorageService(mock_page)
    await storage.set("atomic_test", 999)
    await storage.flush()

    storage_file = Path(tmp_path) / "asase" / "storage.json"
    assert storage_file.exists()
    assert b"atomic_test" in storage_file.read_bytes()
