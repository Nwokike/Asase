"""Platform-resilient key-value storage service for Asase.

Combines Sherlock's web client_storage persistence with KTV Player's
atomic crash-proof local JSON storage and backup rotation.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import flet as ft

logger = logging.getLogger("asase.storage")

storage_env = os.getenv("FLET_APP_STORAGE_DATA")
if storage_env:
    _STORAGE_DIR = Path(storage_env) / "asase"
else:
    _STORAGE_DIR = Path.home() / ".asase"

_STORAGE_FILE = _STORAGE_DIR / "storage.json"
_WRITE_DEBOUNCE_SEC = 1.0


class StorageService:
    """Universal persistent storage engine for Web, Android, and Desktop."""

    def __init__(self, page: ft.Page):
        self._page = page
        self._data: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._dirty = False
        self._last_write: float = 0.0
        self._pending_write_task: asyncio.Task | None = None
        self._is_web = bool(getattr(page, "session_id", None))

        if self._is_web:
            self._load_web()
        else:
            self._load()

    def _load_web(self) -> None:
        try:
            cs = self._page.client_storage
            raw = cs.get("asase_storage")
            self._data = json.loads(raw) if raw else {}
        except Exception as e:
            logger.warning("StorageService._load_web failed: %s", e)
            self._data = {}

    def _load(self) -> None:
        _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        if _STORAGE_FILE.exists():
            try:
                raw = _STORAGE_FILE.read_bytes()
                if raw:
                    self._data = json.loads(raw.decode("utf-8"))
                    return
            except Exception:
                logger.warning("Storage file corrupted. Attempting recovery.")
                bak = _STORAGE_FILE.with_suffix(".json.corrupted")
                with contextlib.suppress(Exception):
                    _STORAGE_FILE.replace(bak)

        bak_file = _STORAGE_FILE.with_suffix(".json.bak")
        if bak_file.exists():
            try:
                raw = bak_file.read_bytes()
                if raw:
                    self._data = json.loads(raw.decode("utf-8"))
                    return
            except Exception:
                pass
        self._data = {}

    def _save_now(self) -> None:
        if self._is_web:
            self._save_now_web()
            return
        try:
            _STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            data_bytes = json.dumps(self._data, ensure_ascii=False, indent=2).encode(
                "utf-8"
            )
            tmp_path = _STORAGE_FILE.with_suffix(".json.tmp")
            bak_path = _STORAGE_FILE.with_suffix(".json.bak")

            if _STORAGE_FILE.exists():
                old = _STORAGE_FILE.read_bytes()
                if old != data_bytes:
                    bak_path.write_bytes(old)

            tmp_path.write_bytes(data_bytes)
            tmp_path.replace(_STORAGE_FILE)
            self._dirty = False
            self._last_write = time.monotonic()
        except Exception as e:
            logger.warning("StorageService._save_now failed: %s", e)

    def _save_now_web(self) -> None:
        try:
            cs = self._page.client_storage
            cs.set("asase_storage", json.dumps(self._data))
            self._dirty = False
            self._last_write = time.monotonic()
        except Exception as e:
            logger.warning("StorageService._save_now_web failed: %s", e)

    def _schedule_write(self) -> None:
        if self._pending_write_task:
            return
        try:
            loop = asyncio.get_event_loop()
            self._pending_write_task = loop.call_later(
                _WRITE_DEBOUNCE_SEC,
                lambda: loop.create_task(self._flush_task()),
            )
        except Exception:
            pass

    async def _flush_task(self) -> None:
        try:
            await self.flush()
        finally:
            self._pending_write_task = None

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._data.get(key, default)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._data[key] = value
            self._dirty = True
        self._schedule_write()

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)
            self._dirty = True
        self._schedule_write()

    async def flush(self) -> None:
        async with self._lock:
            if self._dirty:
                self._save_now()
