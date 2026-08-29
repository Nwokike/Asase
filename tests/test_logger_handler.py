"""Tests for in-memory logging and ring-buffer handler."""

import logging

from core.logger_handler import MemoryLogHandler, in_memory_log_handler


def test_memory_log_handler_emit_and_retrieve():
    MemoryLogHandler.clear_logs()
    assert len(MemoryLogHandler.get_logs()) == 0

    test_logger = logging.getLogger("asase.test_unit")
    test_logger.setLevel(logging.INFO)

    # Directly emit via handler or logger
    record1 = logging.LogRecord(
        "asase.test_unit",
        logging.INFO,
        "",
        0,
        "Planetary telemetry initialized",
        (),
        None,
    )
    record2 = logging.LogRecord(
        "asase.test_unit",
        logging.WARNING,
        "",
        0,
        "Seismic alert threshold triggered",
        (),
        None,
    )

    in_memory_log_handler.emit(record1)
    in_memory_log_handler.emit(record2)

    logs = MemoryLogHandler.get_logs()
    assert len(logs) >= 2
    assert any("Planetary telemetry initialized" in line for line in logs)
    assert any("Seismic alert threshold triggered" in line for line in logs)


def test_memory_log_handler_ring_buffer_cap():
    MemoryLogHandler.clear_logs()
    for i in range(700):
        record = logging.LogRecord(
            "asase.stress", logging.INFO, "", 0, f"Log entry #{i}", (), None
        )
        in_memory_log_handler.emit(record)

    logs = MemoryLogHandler.get_logs()
    # Ring buffer is capped at maxlen=600
    assert len(logs) == 600
    assert "Log entry #699" in logs[-1]
