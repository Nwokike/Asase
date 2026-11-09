"""Shared plumbing for Asase's pydantic-free feed models.

`DataModel` gives every frozen dataclass the `model_validate` /
`model_validate_json` / `model_dump` surface the services were written
against, so swapping pydantic out needed no service changes.

Nested model lists are strict: one bad element raises, so the whole
record is skipped — exactly the pydantic behavior the fail-open tests
lock in (a malformed record never poisons the batch; it just disappears).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import fields
from typing import Any, ClassVar


class DataModel:
    """Base for the feed dataclasses: dump + strict parse entry points.

    Subclasses may declare ``_COMPUTED`` with the names of read-only
    properties that must ride along in ``model_dump()`` — pydantic's
    ``@computed_field`` included them, and the UI reads them from dumps.
    """

    _COMPUTED: ClassVar[tuple[str, ...]] = ()

    def model_dump(self) -> dict:
        out: dict = {}
        for f in fields(self):  # type: ignore[arg-type]
            v = getattr(self, f.name)
            out[f.name] = v.model_dump() if hasattr(v, "model_dump") else v
        for name in self._COMPUTED:
            out[name] = getattr(self, name)
        return out

    @classmethod
    def model_validate(cls, data: Any):
        raise NotImplementedError

    @classmethod
    def model_validate_json(cls, raw: bytes | str):
        try:
            data = json.loads(raw)
        except (ValueError, TypeError) as ex:
            raise ValueError(f"invalid JSON payload: {ex}") from ex
        return cls.model_validate(data)


def parse_models(data: dict, key: str, build: Callable[[Any], Any]) -> list:
    """Parse `data[key]` as a list of nested models — strict on bad items."""
    from models._coerce import opt_list

    return [build(item) for item in opt_list(data, key)]
