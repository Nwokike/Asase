"""Stdlib-only field coercion for Asase's feed models (pydantic-free).

The semantics mirror the pydantic v2 lax behavior the services rely on:

- a missing key or an explicit ``None`` falls back to the field default
  (upstream nulls never reject a record — see tests/test_feeds_failopen.py)
- a present-but-wrong-typed value raises :class:`CoerceError`, so the
  services' per-record ``try/except`` skips exactly the records pydantic's
  ``ValidationError`` used to skip (bad record → fail open, batch survives)
- nested model lists are strict: one bad element raises, so a malformed
  collection still falls back to per-record parsing (USGS slow path)

Only JSON-feed shapes are handled: bools are never numbers (pydantic v2
agrees), numeric strings are rejected rather than silently coerced.
"""

from __future__ import annotations


class CoerceError(ValueError):
    """A field's value cannot be validated — the record must be skipped."""


def _present(data: dict, key: str) -> bool:
    return key in data and data[key] is not None


def as_float(data: dict, key: str) -> float:
    v = data.get(key)
    if v is None:
        raise CoerceError(f"{key}: required float missing")
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise CoerceError(f"{key}: expected number, got {type(v).__name__}")
    return float(v)


def as_int(data: dict, key: str) -> int:
    v = data.get(key)
    if v is None:
        raise CoerceError(f"{key}: required int missing")
    if isinstance(v, bool):
        raise CoerceError(f"{key}: bool is not an int")
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    raise CoerceError(f"{key}: expected int, got {type(v).__name__}")


def as_str(data: dict, key: str) -> str:
    v = data.get(key)
    if v is None:
        raise CoerceError(f"{key}: required string missing")
    if not isinstance(v, str):
        raise CoerceError(f"{key}: expected string, got {type(v).__name__}")
    return v


def opt_float(data: dict, key: str, default: float | None) -> float | None:
    if not _present(data, key):
        return default
    v = data[key]
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise CoerceError(f"{key}: expected number, got {type(v).__name__}")
    return float(v)


def opt_int(data: dict, key: str, default: int | None) -> int | None:
    if not _present(data, key):
        return default
    v = data[key]
    if isinstance(v, bool):
        raise CoerceError(f"{key}: bool is not an int")
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    raise CoerceError(f"{key}: expected int, got {type(v).__name__}")


def opt_str(data: dict, key: str, default: str) -> str:
    if not _present(data, key):
        return default
    v = data[key]
    if not isinstance(v, str):
        raise CoerceError(f"{key}: expected string, got {type(v).__name__}")
    return v


def opt_list(data: dict, key: str) -> list:
    v = data.get(key)
    if v is None:
        return []
    if not isinstance(v, list):
        raise CoerceError(f"{key}: expected list, got {type(v).__name__}")
    return v


def opt_dict(data: dict, key: str) -> dict:
    v = data.get(key)
    if v is None:
        return {}
    if not isinstance(v, dict):
        raise CoerceError(f"{key}: expected object, got {type(v).__name__}")
    return v


def opt_float_list(data: dict, key: str, default=()) -> list:
    """List of numbers (None-able elements allowed) — bad element raises."""
    v = data.get(key)
    if v is None:
        return list(default)
    if not isinstance(v, list):
        raise CoerceError(f"{key}: expected list, got {type(v).__name__}")
    for item in v:
        if item is None:
            continue
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise CoerceError(f"{key}: expected numbers, got {type(item).__name__}")
    return v
