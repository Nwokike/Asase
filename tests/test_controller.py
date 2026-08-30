"""Controller refresh/select/bookmark logic."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from core.controller import AppController
from core.state import state


@pytest.fixture(autouse=True)
def isolate_state():
    orig: dict[str, object] = {
        "lat": state.current_lat,
        "lon": state.current_lon,
        "name": state.current_location_name,
    }
    yield
    state.current_lat, state.current_lon, state.current_location_name = (
        orig["lat"],  # type: ignore[assignment]
        orig["lon"],  # type: ignore[assignment]
        orig["name"],  # type: ignore[assignment]
    )
    state.earthquakes, state.disasters = [], []
    state.weather_data, state.air_quality_data, state.flood_data, state.marine_data = (
        {},
        {},
        {},
        {},
    )
    state.space_weather, state.bookmarks, state.recent_searches = {}, [], []
    state.is_online, state.is_loading = True, False


def _page_mock(web=False):
    m = MagicMock()
    m.web = web
    m.session_id = None
    m.theme_mode = MagicMock()
    m.services = []
    m.render = MagicMock()
    m.update = MagicMock()
    m.run_task = MagicMock()
    m.client_storage = MagicMock()
    m.client_storage.get.return_value = None
    return m


@pytest.mark.asyncio
async def test_refresh_offline_skip():
    page = _page_mock()
    c = AppController(page)
    c.storage = AsyncMock()
    state.is_online = False
    await c.refresh_all()
    assert state.is_loading is False
    c.storage.get_cached_telemetry.assert_not_called()


@pytest.mark.asyncio
async def test_toggle_bookmark_add_and_remove():
    page = _page_mock()
    c = AppController(page)
    c.storage = AsyncMock()
    c.haptics = None
    loc = {"name": "Lagos", "latitude": 6.5, "longitude": 3.3}
    await c.toggle_bookmark(loc)
    assert any(b["name"] == "Lagos" for b in state.bookmarks)
    await c.toggle_bookmark(loc)
    assert not any(b["name"] == "Lagos" for b in state.bookmarks)


@pytest.mark.asyncio
async def test_toggle_bookmark_no_name_noop():
    page = _page_mock()
    c = AppController(page)
    c.storage = AsyncMock()
    c.haptics = None
    await c.toggle_bookmark({})
    assert state.bookmarks == []
