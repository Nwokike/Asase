"""Task-scheduling hygiene guard (Batch L).

All UI-layer coroutines go through core.tasks.schedule (page.run_task when
a page is in scope, else create_task with a logging done-callback) so
background failures are never silent.
"""

import re
from pathlib import Path

UI_DIRS = [Path("src/screens"), Path("src/components")]


def _py_files():
    for d in UI_DIRS:
        yield from d.rglob("*.py")


def test_no_raw_create_task_in_ui_layer():
    offenders = []
    for f in _py_files():
        for i, line in enumerate(f.read_text().splitlines(), 1):
            if "asyncio.create_task" in line:
                offenders.append(f"{f}:{i}")
    assert offenders == [], f"raw asyncio.create_task found: {offenders}"


def test_no_bare_import_asyncio_without_use():
    offenders = []
    for f in _py_files():
        text = f.read_text()
        if re.search(
            r"^import asyncio$", text, re.MULTILINE
        ) and "asyncio." not in text.replace("import asyncio", "", 1):
            offenders.append(str(f))
    assert offenders == [], f"unused asyncio import: {offenders}"


def test_schedule_prefers_page_run_task():
    from unittest.mock import MagicMock

    from core.tasks import schedule

    async def _fn(a, b=0):
        return (a, b)

    page = MagicMock()
    result = schedule(_fn, 1, b=2, page=page)
    page.run_task.assert_called_once_with(_fn, 1, b=2)
    assert result is page.run_task.return_value


def test_schedule_fallback_logs_failures(caplog):
    import asyncio
    import logging

    from core.tasks import schedule

    async def _boom():
        raise RuntimeError("boom")

    async def _run():
        task = schedule(_boom)
        try:
            await task
        except RuntimeError:
            pass

    with caplog.at_level(logging.WARNING, logger="asase.tasks"):
        asyncio.new_event_loop().run_until_complete(_run())
    assert any("Background task failed" in r.message for r in caplog.records)
