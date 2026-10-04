"""Dossier radius-history loader regressions.

Behavioral: exercises the REAL loader (`fetch_radius_history_events`)
that ReportScreen's auto-load effect runs, including the fail-open
contract (no callback / empty result / transport error → []).
"""

from unittest.mock import AsyncMock

from screens.report_screen import fetch_radius_history_events


async def test_loader_passes_radius_and_returns_events():
    fetch = AsyncMock(return_value=[{"magnitude": 4.2, "place": "Near Enugu"}])
    evs = await fetch_radius_history_events(fetch, 6.44, 7.50)
    fetch.assert_awaited_once_with(6.44, 7.50, 500.0)
    assert evs == [{"magnitude": 4.2, "place": "Near Enugu"}]


async def test_loader_without_callback_returns_empty():
    assert await fetch_radius_history_events(None, 6.44, 7.50) == []


async def test_loader_failure_failopens_to_empty():
    fetch = AsyncMock(side_effect=RuntimeError("boom"))
    assert await fetch_radius_history_events(fetch, 6.44, 7.50) == []


async def test_loader_none_result_failopens_to_empty():
    fetch = AsyncMock(return_value=None)
    assert await fetch_radius_history_events(fetch, 6.44, 7.50) == []
