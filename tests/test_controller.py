"""Controller refresh/select/bookmark logic."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.controller import AppController
from core.state import state


@pytest.fixture(autouse=True)
def isolate_state():
    orig: dict[str, object] = {
        "lat": state.current_lat,
        "lon": state.current_lon,
        "name": state.current_location_name,
        "country": state.current_country,
        "elevation": state.current_elevation,
    }
    yield
    (
        state.current_lat,
        state.current_lon,
        state.current_location_name,
        state.current_country,
        state.current_elevation,
    ) = (
        orig["lat"],  # type: ignore[assignment]
        orig["lon"],  # type: ignore[assignment]
        orig["name"],  # type: ignore[assignment]
        orig["country"],  # type: ignore[assignment]
        orig["elevation"],  # type: ignore[assignment]
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


@pytest.mark.asyncio
async def test_auto_locate_on_startup_uses_device_gps():
    from unittest.mock import patch

    from core.device_services import DeviceServices

    page = _page_mock()
    c = AppController(page)
    state.current_location_name = "Global Telemetry"

    with (
        patch.object(
            DeviceServices,
            "locate_user",
            new=AsyncMock(),
        ) as mock_locate,
        patch.object(c, "refresh_all", new=AsyncMock()),
    ):
        await c._auto_locate_on_startup()

    mock_locate.assert_awaited_once()
    assert mock_locate.call_args.args[0] is c.geolocator


@pytest.mark.asyncio
async def test_auto_locate_on_startup_skipped_on_web():
    # Browsers suppress permission prompts without a user gesture — on web,
    # locality must come from the onboarding GPS button or search bar instead.
    page = _page_mock(web=True)
    c = AppController(page)

    async def _fail(*args, **kwargs):
        raise AssertionError("locate_user must not run on web startup")

    c.locate_user = _fail
    state.current_location_name = "Global Telemetry"
    await c._auto_locate_on_startup()


@pytest.mark.asyncio
async def test_select_coordinates_refreshes_local_feeds_only():
    page = _page_mock()
    c = AppController(page)
    c.storage = AsyncMock()
    c.haptics = None
    c.ad_service = None

    with (
        patch.object(c, "refresh_local_feeds", new=AsyncMock()) as mock_local,
        patch.object(c, "refresh_all", new=AsyncMock()) as mock_all,
        patch(
            "services.geocoding_service.GeocodingService.get_elevation",
            new=AsyncMock(return_value=0.0),
        ),
    ):
        await c.select_coordinates(6.5, 3.4, "Lagos", "Nigeria")

    mock_local.assert_awaited_once()
    mock_all.assert_not_awaited()
    assert state.current_location_name == "Lagos"


@pytest.mark.asyncio
async def test_select_coordinates_persists_last_location():
    page = _page_mock()
    c = AppController(page)
    c.storage = AsyncMock()
    c.haptics = None
    c.ad_service = None

    with (
        patch.object(c, "refresh_local_feeds", new=AsyncMock()),
        patch(
            "services.geocoding_service.GeocodingService.get_elevation",
            new=AsyncMock(return_value=42.0),
        ),
    ):
        await c.select_coordinates(9.08, 7.40, "Abuja", "Nigeria", silent=True)

    keys = [call.args[0] for call in c.storage.set.await_args_list]
    assert "asase.last_location" in keys


@pytest.mark.asyncio
async def test_refresh_coalesces_instead_of_dropping():
    # A request arriving mid-flight queues one extra pass so the freshest
    # state (e.g. a city picked during startup refresh) is always fetched.
    page = _page_mock()
    c = AppController(page)
    c.storage = AsyncMock()

    calls: list = []

    async def _slow_global():
        calls.append("global")
        await asyncio.sleep(0.05)

    with (
        patch.object(c, "_fetch_global_feeds", new=_slow_global),
        patch.object(c, "_fetch_local_feeds", new=AsyncMock()),
        patch("core.controller.show_snack"),
    ):
        first = asyncio.create_task(c.refresh_all())
        await asyncio.sleep(0.01)
        await c.refresh_all()  # arrives mid-flight
        await first

    assert calls.count("global") == 2
