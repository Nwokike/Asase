"""Storage + logger wiring regressions (Batch K)."""

import logging
from unittest.mock import MagicMock

import pytest

from core.logger_handler import (
    MemoryLogHandler,
    setup_in_memory_logging,
)


def test_setup_is_idempotent_across_calls():
    first = setup_in_memory_logging()
    second = setup_in_memory_logging()
    assert first is second
    count = sum(isinstance(h, MemoryLogHandler) for h in logging.getLogger().handlers)
    assert count == 1


def test_setup_clears_previous_session_logs():
    MemoryLogHandler._logs.append("stale from last session")
    setup_in_memory_logging()
    assert MemoryLogHandler.get_logs() == []


def _web_page(*, fail_mount=False):
    page = MagicMock()
    page.web = True
    if fail_mount:
        page.services.append.side_effect = RuntimeError("service add failed")
    else:
        page.services = []
    return page


def test_web_mount_failure_disables_persistence_loudly(caplog):
    from services.storage_service import StorageService

    page = _web_page(fail_mount=True)
    with caplog.at_level(logging.ERROR, logger="asase.storage"):
        svc = StorageService(page)
    assert svc._web_persistence_available is False
    assert any("mount failed" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_web_save_after_failed_mount_is_noop():
    from services.storage_service import StorageService

    page = _web_page(fail_mount=True)
    svc = StorageService(page)
    svc._data = {"k": "v"}
    svc._dirty = True
    await svc.flush()  # must not raise, must not clear dirty
    assert svc._dirty is True


def test_schedule_write_without_running_loop_writes_through(tmp_path, monkeypatch):
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path))
    from services.storage_service import StorageService

    page = MagicMock()
    page.web = False
    svc = StorageService(page)
    svc._data = {"k": "v"}
    svc._dirty = True
    # No running loop in a sync test -> sync write-through, no drop.
    svc._schedule_write()
    assert svc._dirty is False
