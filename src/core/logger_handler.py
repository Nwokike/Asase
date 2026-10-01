"""In-memory ring-buffer log handler for live Activity Terminal."""

from __future__ import annotations

import logging
from collections import deque
from typing import ClassVar


class MemoryLogHandler(logging.Handler):
    """In-memory ring-buffer log handler for live Activity Terminal."""

    _logs: ClassVar[deque[str]] = deque(maxlen=600)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            MemoryLogHandler._logs.append(msg)
        except Exception:
            self.handleError(record)

    @classmethod
    def get_logs(cls) -> list[str]:
        return list(cls._logs)

    @classmethod
    def clear_logs(cls) -> None:
        cls._logs.clear()


def _build_handler() -> MemoryLogHandler:
    handler = MemoryLogHandler()
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S"
        )
    )
    return handler


def setup_in_memory_logging() -> MemoryLogHandler:
    """Attach the ring-buffer handler to the root logger, idempotently.

    The isinstance scan (not identity ``not in``) also dedups across
    module reloads; a fresh session starts with a cleared buffer so the
    Activity Terminal never shows the previous session's logs.
    """
    global in_memory_log_handler
    root_logger = logging.getLogger()
    for existing in root_logger.handlers:
        if isinstance(existing, MemoryLogHandler):
            in_memory_log_handler = existing
            existing.clear_logs()
            return existing
    in_memory_log_handler = _build_handler()
    root_logger.addHandler(in_memory_log_handler)
    return in_memory_log_handler


# Attach to root logger at import (kept for back-compat with existing
# `from core.logger_handler import in_memory_log_handler` imports).
in_memory_log_handler = setup_in_memory_logging()
