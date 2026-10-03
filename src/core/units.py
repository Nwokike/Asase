"""Unit preferences — single choke point for temperature/speed display.

State holds canonical lowercase values (``temp_unit`` in {"celsius",
"fahrenheit"}, ``speed_unit`` in {"kmh", "mph"}); every formatter in the
app goes through here so the Settings screen choices actually render.
"""

from __future__ import annotations

from core.state import state


def _num(value: object) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def safe_float(value: object, default=None) -> float | None:
    """Coerce upstream feed values to float; None/'--'/'' -> default.

    Feed sentinels are truthy-or-None but not numeric, so truthiness
    checks never guard ``float(value or 0)``. Every numeric extraction
    goes through here.
    """
    if value is None or value == "":
        return default
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def format_temp(celsius: object) -> str:
    """Format a Celsius reading per the user's temperature preference."""
    value = _num(celsius)
    if value is None:
        return "n/a"
    if state.temp_unit == "fahrenheit":
        return f"{value * 9.0 / 5.0 + 32.0:.0f}°F"
    return f"{value:.0f}°C"


def format_temp_verbose(celsius: object) -> str:
    """Long-form temperature for dossier/export text (shows both units)."""
    value = _num(celsius)
    if value is None:
        return "n/a"
    fahrenheit = value * 9.0 / 5.0 + 32.0
    return f"{value:.1f}°C ({fahrenheit:.1f}°F)"


def format_speed(kmh: object) -> str:
    """Format a km/h reading per the user's speed preference."""
    value = _num(kmh)
    if value is None:
        return "n/a"
    if state.speed_unit == "mph":
        return f"{value * 0.621371:.0f} mph"
    return f"{value:.0f} km/h"


def format_speed_verbose(kmh: object) -> str:
    """Long-form speed for dossier/export text (shows both units)."""
    value = _num(kmh)
    if value is None:
        return "n/a"
    mph = value * 0.621371
    return f"{value:.1f} km/h ({mph:.1f} mph)"


def format_feed_age(updated_at: float | None, now: float | None = None) -> str:
    """Human age for a feed timestamp ("just now", "4m ago", "2h ago").

    ``None`` (never fetched) renders as "—" so chips degrade honestly.
    """
    import time as _time

    if updated_at is None:
        return "—"
    try:
        age = max(0.0, (now if now is not None else _time.time()) - float(updated_at))
    except (TypeError, ValueError):
        return "—"
    if age < 60:
        return "just now"
    if age < 3600:
        return f"{int(age // 60)}m ago"
    if age < 86400:
        return f"{int(age // 3600)}h ago"
    return f"{int(age // 86400)}d ago"


def feed_age(source: str, now: float | None = None) -> str:
    """Age chip text for a feed source key in ``state.feed_updated``."""
    return format_feed_age(state.feed_updated.get(source), now)
