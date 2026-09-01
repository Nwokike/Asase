"""Platform-resilient key-value storage & Gzip telemetry cache service for Asase.

Combines:
1. Sherlock's web client_storage persistence
2. KTV Player's atomic crash-proof local JSON storage (.tmp + .bak + .corrupted)
3. L1 Memory LRU Cache + L2 Disk Gzip (.json.gz) telemetry cache with TTL
"""

from __future__ import annotations

import asyncio
import collections
import contextlib
import gzip
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import flet as ft
import msgpack

logger = logging.getLogger("asase.storage")

_WRITE_DEBOUNCE_SEC = 1.0


def get_storage_dir() -> Path:
    storage_env = os.getenv("FLET_APP_STORAGE_DATA")
    if storage_env:
        return Path(storage_env) / "asase"
    return Path.home() / ".asase"


def get_storage_file() -> Path:
    return get_storage_dir() / "storage.json"


def get_cache_dir() -> Path:
    d = get_storage_dir() / "cache" / "telemetry"
    d.mkdir(parents=True, exist_ok=True)
    return d


class StorageService:
    """Universal persistent storage & multi-tier cache engine for Web, Android, and Desktop."""

    def __init__(self, page: ft.Page):
        self._page = page
        self._data: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._dirty = False
        self._last_write: float = 0.0
        self._pending_write_task: asyncio.Task | None = None
        self._is_web = bool(getattr(page, "session_id", None))

        # L1 Memory LRU Cache
        self._l1_cache: collections.OrderedDict[str, dict[str, Any]] = (
            collections.OrderedDict()
        )
        self._max_l1_items = 50

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
        storage_dir = get_storage_dir()
        storage_file = get_storage_file()
        storage_dir.mkdir(parents=True, exist_ok=True)
        if storage_file.exists():
            try:
                raw = storage_file.read_bytes()
                if raw:
                    self._data = json.loads(raw.decode("utf-8"))
                    return
            except Exception:
                logger.warning("Storage file corrupted. Attempting recovery.")
                bak = storage_file.with_suffix(".json.corrupted")
                with contextlib.suppress(Exception):
                    storage_file.replace(bak)

        bak_file = storage_file.with_suffix(".json.bak")
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
            storage_dir = get_storage_dir()
            storage_file = get_storage_file()
            storage_dir.mkdir(parents=True, exist_ok=True)
            data_bytes = json.dumps(
                self._data, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            tmp_path = storage_file.with_suffix(".json.tmp")
            bak_path = storage_file.with_suffix(".json.bak")

            if storage_file.exists():
                old = storage_file.read_bytes()
                if old != data_bytes:
                    bak_path.write_bytes(old)

            tmp_path.write_bytes(data_bytes)
            tmp_path.replace(storage_file)
            self._dirty = False
            self._last_write = time.monotonic()
        except Exception as e:
            logger.warning("StorageService._save_now failed: %s", e)

    def _save_now_web(self) -> None:
        try:
            cs = self._page.client_storage
            cs.set("asase_storage", json.dumps(self._data, separators=(",", ":")))
            self._dirty = False
            self._last_write = time.monotonic()
        except Exception as e:
            logger.warning("StorageService._save_now_web failed: %s", e)

    def _schedule_write(self) -> None:
        if self._pending_write_task and not self._pending_write_task.done():
            self._pending_write_task.cancel()
        try:
            loop = asyncio.get_event_loop()
            self._pending_write_task = loop.create_task(self._debounced_flush())
        except RuntimeError:
            pass

    async def _debounced_flush(self) -> None:
        try:
            await asyncio.sleep(_WRITE_DEBOUNCE_SEC)
            await self.flush()
        except asyncio.CancelledError:
            pass
        finally:
            self._pending_write_task = None

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
                await asyncio.to_thread(self._save_now)

    # ── High-Performance MsgPack Telemetry Cache Subsystem ──

    def _cache_path(self, key: str) -> Path:
        h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
        return get_cache_dir() / f"{h}.msgpack"

    async def get_cached_telemetry(self, key: str) -> Any | None:
        """Retrieve telemetry from L1 Memory or L2 Disk MsgPack Cache (with legacy fallback)."""
        now = time.time()
        # 1. L1 Memory
        if key in self._l1_cache:
            item = self._l1_cache[key]
            if now < item["expires_at"]:
                self._l1_cache.move_to_end(key)
                return item["data"]
            del self._l1_cache[key]

        # 2. L2 Disk MsgPack (with legacy gzip fallback)
        if not self._is_web:
            path = self._cache_path(key)
            h = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
            legacy_path = get_cache_dir() / f"{h}.json.gz"

            if path.exists():
                try:
                    raw = await asyncio.to_thread(path.read_bytes)
                    envelope = msgpack.unpackb(raw, raw=False)
                    if now < envelope.get("expires_at", 0):
                        data = envelope.get("data")
                        self._l1_cache[key] = {
                            "data": data,
                            "expires_at": envelope["expires_at"],
                        }
                        if len(self._l1_cache) > self._max_l1_items:
                            self._l1_cache.popitem(last=False)
                        return data
                    await asyncio.to_thread(path.unlink, True)
                except Exception as e:
                    logger.debug("MsgPack cache read error for %s: %s", key, e)
                    with contextlib.suppress(Exception):
                        await asyncio.to_thread(path.unlink, True)
            elif legacy_path.exists():
                try:
                    raw = await asyncio.to_thread(legacy_path.read_bytes)
                    decompressed = await asyncio.to_thread(gzip.decompress, raw)
                    envelope = json.loads(decompressed.decode("utf-8"))
                    if now < envelope.get("expires_at", 0):
                        data = envelope.get("data")
                        self._l1_cache[key] = {
                            "data": data,
                            "expires_at": envelope["expires_at"],
                        }
                        if len(self._l1_cache) > self._max_l1_items:
                            self._l1_cache.popitem(last=False)
                        return data
                    await asyncio.to_thread(legacy_path.unlink, True)
                except Exception as e:
                    logger.debug("Legacy cache read error for %s: %s", key, e)
                    with contextlib.suppress(Exception):
                        await asyncio.to_thread(legacy_path.unlink, True)
        return None

    async def set_cached_telemetry(
        self,
        key: str,
        data: Any,
        ttl_seconds: float = 900.0,
        ttl: float | None = None,
    ) -> None:
        """Store telemetry in L1 Memory and L2 Disk MsgPack Cache (3-5x faster binary format)."""
        actual_ttl = ttl if ttl is not None else ttl_seconds
        expires_at = time.time() + actual_ttl
        if len(self._l1_cache) >= self._max_l1_items:
            self._l1_cache.popitem(last=False)
        self._l1_cache[key] = {"data": data, "expires_at": expires_at}

        if not self._is_web:
            try:
                envelope = {
                    "key": key,
                    "expires_at": expires_at,
                    "data": data,
                }
                packed = msgpack.packb(envelope, use_bin_type=True)
                path = self._cache_path(key)
                tmp_path = path.with_suffix(".tmp")

                def _write() -> None:
                    tmp_path.write_bytes(packed)
                    tmp_path.replace(path)

                await asyncio.to_thread(_write)
            except Exception as e:
                logger.debug("Cache write error for %s: %s", key, e)
