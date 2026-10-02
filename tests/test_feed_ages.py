"""Feed timestamp + age formatter regressions (D2 Batch 1)."""

import time

from core.state import state
from core.units import feed_age, format_feed_age


def test_format_feed_age_boundaries():
    now = time.time()
    assert format_feed_age(None) == "—"
    assert format_feed_age("junk") == "—"
    assert format_feed_age(now, now) == "just now"
    assert format_feed_age(now - 30, now) == "just now"
    assert format_feed_age(now - 240, now) == "4m ago"
    assert format_feed_age(now - 7200, now) == "2h ago"
    assert format_feed_age(now - 90000, now) == "1d ago"
    assert format_feed_age(now + 9999, now) == "just now"  # clock skew


def test_feed_age_reads_state():
    state.feed_updated = {}
    assert feed_age("usgs") == "—"
    state.feed_updated = {**state.feed_updated, "usgs": time.time() - 60}
    assert feed_age("usgs") == "1m ago"
    state.feed_updated = {}


def test_refresh_stamps_feed_timestamps():
    import asyncio
    from unittest.mock import AsyncMock, MagicMock, patch

    from core.controller import AppController

    async def _run():
        page = MagicMock()
        page.web = True
        c = AppController(page)
        c.storage = AsyncMock()
        with (
            patch(
                "services.seismic_service.SeismicService.fetch_earthquakes",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "services.disaster_service.DisasterService.fetch_active_disasters",
                new=AsyncMock(return_value=[]),
            ),
            patch(
                "services.space_weather_service.SpaceWeatherService.fetch_space_weather",
                new=AsyncMock(return_value={}),
            ),
        ):
            state.feed_updated = {}
            await c._fetch_global_feeds()
        stamped = dict(state.feed_updated)
        state.feed_updated = {}
        return stamped

    stamped = asyncio.new_event_loop().run_until_complete(_run())
    assert set(stamped) == {"usgs", "eonet"}
    assert all(isinstance(v, float) for v in stamped.values())
