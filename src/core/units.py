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


def format_temp(celsius: object) -> str:
    """Format a Celsius reading per the user's temperature preference."""
    value = _num(celsius)
    if value is None:
        return "n/a"
    if state.temp_unit == "fahrenheit":
        return f"{value * 9.0 / 5.0 + 32.0:.0f}°F"
    return f"{value:.0f}°C"


def format_speed(kmh: object) -> str:
    """Format a km/h reading per the user's speed preference."""
    value = _num(kmh)
    if value is None:
        return "n/a"
    if state.speed_unit == "mph":
        return f"{value * 0.621371:.0f} mph"
    return f"{value:.0f} km/h"


def format_speed_verbose(kmh: object) -> str:
    """Long-form speed for dossier/export text."""
    value = _num(kmh)
    if value is None:
        return "n/a"
    if state.speed_unit == "mph":
        return f"{value * 0.621371:.0f} mph"
    return f"{value:.0f} km/h"
