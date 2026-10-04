"""HTTP conditional-request helper (ETag / Last-Modified).

Poll-heavy feeds (USGS, EONET, Open-Meteo) emit cache validators. Keeping
the last validators + body per URL in memory lets refreshes send
``If-None-Match`` / ``If-Modified-Since`` and skip re-download + re-parse
entirely on 304. Records are process-memory (a restart simply makes the
next fetch unconditional) — no signature changes, no storage dependency.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from core.network import NetworkManager

logger = logging.getLogger("asase.validators")

# Validators older than this are not sent (feeds rotate them silently).
_MAX_VALIDATOR_AGE_SEC = 3600.0

_records: dict[str, dict[str, Any]] = {}
_MAX_RECORDS = 50  # LRU-ish cap: dynamic URLs (radius queries) must not leak


def _headers_for(url: str) -> dict[str, str]:
    record = _records.get(url)
    if not record:
        return {}
    if time.time() - record.get("saved_at", 0) > _MAX_VALIDATOR_AGE_SEC:
        _records.pop(url, None)
        return {}
    headers: dict[str, str] = {}
    if record.get("etag"):
        headers["If-None-Match"] = record["etag"]
    if record.get("last_modified"):
        headers["If-Modified-Since"] = record["last_modified"]
    return headers


def _remember(url: str, res) -> None:
    if len(_records) >= _MAX_RECORDS:
        # Insertion-ordered dict: drop the oldest entry.
        for oldest in list(_records)[: len(_records) - _MAX_RECORDS + 1]:
            _records.pop(oldest, None)
    # Re-insert to refresh recency: a plain reassignment keeps the original
    # insertion slot, so hot feeds would evict before one-shot URLs.
    _records.pop(url, None)
    _records[url] = {
        "etag": res.headers.get("etag"),
        "last_modified": res.headers.get("last-modified"),
        "saved_at": time.time(),
    }


def clear_records() -> None:
    """Test hook: drop all cached validators."""
    _records.clear()


async def conditional_get_json(
    url: str,
    *,
    timeout=None,
    log_name: str = "feed",
) -> tuple[int, Any | None]:
    """GET with validators; returns (status_code, parsed_json_or_None).

    On 304 the previously stored body is returned with status 304 — callers
    parse it exactly like a 200. Any failure degrades to (0, None) so
    callers keep their existing fail-soft paths untouched.
    """
    headers = _headers_for(url)
    try:
        client = NetworkManager.get_client()
        kwargs: dict[str, Any] = {"headers": headers} if headers else {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        res = await client.get(url, **kwargs)
        if res.status_code == 304:
            record = _records.get(url, {})
            if record.get("body") is not None:
                logger.debug("%s unchanged (304): %s", log_name, url[:80])
                return 304, record["body"]
            # Validator without a body (shouldn't happen) — treat as miss.
            return 304, None
        if res.status_code == 200:
            try:
                body = res.json()
            except Exception:
                return res.status_code, None
            _remember(url, res)
            _records[url]["body"] = body
            return 200, body
        logger.warning("%s fetch: HTTP %d for %s", log_name, res.status_code, url[:80])
        return res.status_code, None
    except Exception as ex:
        logger.warning("%s fetch failed for %s: %s", log_name, url[:80], ex)
        return 0, None
