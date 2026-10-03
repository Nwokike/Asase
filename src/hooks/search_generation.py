"""SearchGeneration — generation counter for overlapping async searches.

Debounced searches resolve out of order (a slow request started earlier can
finish after a newer one). Each search claims a token from this counter and
may publish its results only while its token is still the newest — stale
responses are dropped instead of overwriting fresher ones.

Hoisted out of the HomeScreen closure so the real protocol is testable.
"""

from __future__ import annotations


class SearchGeneration:
    """Monotonic token source: only the latest generation may publish."""

    __slots__ = ("_current",)

    def __init__(self) -> None:
        self._current = 0

    @property
    def current(self) -> int:
        return self._current

    def begin(self) -> int:
        """Claim a generation; call once per search before awaiting."""
        self._current += 1
        return self._current

    def is_current(self, token: int) -> bool:
        """True iff no newer generation has begun since ``token`` was claimed."""
        return token == self._current
