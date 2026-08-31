"""High-performance network engine with connection pooling, retries, and latency tracing.

Leverages 100% of httpx capabilities: connection pooling (Limits), custom RetryTransport
with exponential backoff and jitter, fine-grained Timeouts, and event hooks for live telemetry tracing.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any, ClassVar

import httpx

logger = logging.getLogger("asase.network")

# Shared connection limits across all planetary feeds
LIMITS = httpx.Limits(
    max_keepalive_connections=20,
    max_connections=50,
    keepalive_expiry=30.0,
)

DEFAULT_TIMEOUT = httpx.Timeout(
    connect=5.0,
    read=15.0,
    write=5.0,
    pool=3.0,
)

AUTOCOMPLETE_TIMEOUT = httpx.Timeout(
    connect=2.5,
    read=5.0,
    write=2.5,
    pool=1.5,
)


class ResilientRetryTransport(httpx.AsyncHTTPTransport):
    """Async transport with jittered exponential backoff for planetary telemetry APIs."""

    RETRIABLE_STATUS_CODES: ClassVar[set[int]] = {429, 500, 502, 503, 504}
    RETRIABLE_EXCEPTIONS: ClassVar[tuple[type[Exception], ...]] = (
        httpx.ConnectError,
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.RemoteProtocolError,
    )

    def __init__(
        self, max_retries: int = 3, backoff_factor: float = 0.5, **kwargs: Any
    ):
        super().__init__(**kwargs)
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        attempt = 0
        while True:
            try:
                response = await super().handle_async_request(request)
                if (
                    response.status_code not in self.RETRIABLE_STATUS_CODES
                    or attempt >= self.max_retries
                ):
                    return response

                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    delay = float(retry_after)
                else:
                    delay = self.backoff_factor * (2**attempt) + random.uniform(
                        0.05, 0.25
                    )

                logger.warning(
                    "HTTP %d from %s — Retrying attempt %d/%d after %.2fs",
                    response.status_code,
                    request.url.host,
                    attempt + 1,
                    self.max_retries,
                    delay,
                )
                await response.aclose()
                await asyncio.sleep(delay)
                attempt += 1
            except self.RETRIABLE_EXCEPTIONS as exc:
                if attempt >= self.max_retries:
                    logger.error(
                        "HTTP request failed after %d retries for %s: %s",
                        attempt,
                        request.url,
                        exc,
                    )
                    raise
                delay = self.backoff_factor * (2**attempt) + random.uniform(0.05, 0.25)
                logger.warning(
                    "Network error (%s) on %s — Retrying attempt %d/%d after %.2fs",
                    type(exc).__name__,
                    request.url.host,
                    attempt + 1,
                    self.max_retries,
                    delay,
                )
                await asyncio.sleep(delay)
                attempt += 1


async def on_request_hook(request: httpx.Request) -> None:
    request.headers["User-Agent"] = "Asase-Earth-Intelligence/1.0 (+https://kiri.ng)"
    request.extensions["start_time"] = time.perf_counter()


async def on_response_hook(response: httpx.Response) -> None:
    start_time = response.request.extensions.get("start_time")
    duration_ms = (time.perf_counter() - start_time) * 1000 if start_time else 0.0

    level = logging.INFO if response.status_code < 400 else logging.WARNING
    logger.log(
        level,
        "[%s] %s -> %d (%.1f ms)",
        response.request.method,
        response.request.url.path,
        response.status_code,
        duration_ms,
    )


class NetworkManager:
    """Singleton HTTP client manager with persistent connection pooling."""

    _instance: NetworkManager | None = None
    _client: httpx.AsyncClient | None = None

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            transport = ResilientRetryTransport(
                max_retries=3,
                backoff_factor=0.4,
                limits=LIMITS,
            )
            cls._client = httpx.AsyncClient(
                transport=transport,
                timeout=DEFAULT_TIMEOUT,
                event_hooks={
                    "request": [on_request_hook],
                    "response": [on_response_hook],
                },
                follow_redirects=True,
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client and not cls._client.is_closed:
            await cls._client.aclose()
            cls._client = None

    @classmethod
    async def close_all(cls) -> None:
        await cls.close()
