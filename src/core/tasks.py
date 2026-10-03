"""Async scheduling helper for UI callbacks.

``page.run_task`` binds the coroutine to the page's event loop and surfaces
exceptions; bare ``asyncio.create_task`` in a sync Flet callback does neither
(failures vanish silently, and the task may land on the wrong loop). Pure
builder functions with no page in scope fall back to ``create_task`` with a
logging done-callback so failures are never silent.

Sync callables (state-setter lambdas like ``controller.go_home``) are
executed directly — they return plain values (often tuples), not coroutines,
so wrapping them in a task raised ``TypeError: a coroutine was expected``.
Failures always log at WARNING so nothing is swallowed.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
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
    """Run ``coro_fn(*args, **kwargs)`` on the page loop when possible.

    Coroutine functions are scheduled (Future via ``page.run_task`` when a
    page is available, Task otherwise). Sync callables are invoked directly
    with their exceptions logged — never silently dropped.
    """
    if not inspect.iscoroutinefunction(coro_fn):
        # Sync path: controller state-setter lambdas etc. Call directly.
        try:
            return coro_fn(*args, **kwargs)
        except Exception:
            logger.warning(
                "Sync callback failed: %s(%r)",
                getattr(coro_fn, "__name__", coro_fn),
                args,
            )
            raise
    if page is not None and hasattr(page, "run_task"):
        try:
            return page.run_task(coro_fn, *args, **kwargs)
        except TypeError:
            # run_task requires a coroutine function — fall through to Task
            pass
        except Exception as ex:
            logger.warning("page.run_task failed (%s); falling back", ex)
    task = asyncio.create_task(coro_fn(*args, **kwargs))
    task.add_done_callback(_log_failure)
    return task
