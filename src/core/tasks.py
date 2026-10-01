"""Async scheduling helper for UI callbacks.

``page.run_task`` binds the coroutine to the page's event loop and surfaces
exceptions; bare ``asyncio.create_task`` in a sync Flet callback does neither
(failures vanish silently, and the task may land on the wrong loop). Pure
builder functions with no page in scope fall back to ``create_task`` with a
logging done-callback so failures are never silent.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

logger = logging.getLogger("asase.tasks")


def _log_failure(task: asyncio.Task) -> None:
    try:
        exc = task.exception()
    except asyncio.CancelledError:
        return
    if exc is not None:
        logger.warning("Background task failed: %s", exc)


def schedule(coro_fn, *args: Any, page=None, **kwargs: Any):
    """Schedule ``coro_fn(*args, **kwargs)`` on the page loop when possible.

    Returns whatever the underlying scheduler returns (a Future for
    ``page.run_task``, a Task otherwise) so callers can await if needed.
    """
    if page is not None and hasattr(page, "run_task"):
        try:
            return page.run_task(coro_fn, *args, **kwargs)
        except Exception as ex:
            logger.debug("page.run_task failed, falling back: %s", ex)
    task = asyncio.create_task(coro_fn(*args, **kwargs))
    task.add_done_callback(_log_failure)
    return task


def schedule_coro(coro: Coroutine, *, page=None):
    """Schedule an already-created coroutine object (for call sites that
    build the coroutine inline). Prefer :func:`schedule` with a function."""
    if page is not None and hasattr(page, "run_task"):
        # run_task needs a coroutine *function* — wrap the object.
        async def _await_it():
            return await coro

        try:
            return page.run_task(_await_it)
        except Exception as ex:
            logger.debug("page.run_task failed, falling back: %s", ex)
    task = asyncio.create_task(coro)
    task.add_done_callback(_log_failure)
    return task
