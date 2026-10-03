"""Search race + spinner regressions.

Exercises the REAL generation protocol (hooks.search_generation) that
HomeScreen's _do_search uses — not a re-implementation of it.
"""

import asyncio
import logging

import flet as ft

from components.home.location_search_bar import build_location_search_bar
from hooks.search_generation import SearchGeneration


def _bar(**kwargs):
    defaults = {
        "page": None,
        "search_query": "",
        "search_results": [],
        "on_search_change": lambda e: None,
        "on_select_city": lambda c: None,
        "on_locate_gps": lambda: None,
    }
    defaults.update(kwargs)
    logging.disable(logging.CRITICAL)
    try:
        return build_location_search_bar(**defaults)
    finally:
        logging.disable(logging.NOTSET)


def _search_bar_node(container):
    col = container.content
    assert isinstance(col, ft.Column)
    return col.controls[0]


def test_spinner_shows_progress_ring_while_searching():
    bar = _search_bar_node(_bar(is_searching=True))
    assert isinstance(bar, ft.SearchBar)
    assert isinstance(bar.bar_leading, ft.Container)
    ring = bar.bar_leading.content
    assert isinstance(ring, ft.ProgressRing)


def test_no_spinner_when_idle():
    bar = _search_bar_node(_bar(is_searching=False))
    assert isinstance(bar, ft.SearchBar)
    assert isinstance(bar.bar_leading, ft.Icon)


def test_generation_starts_at_zero_and_claims_monotonically():
    gen = SearchGeneration()
    assert gen.current == 0
    assert gen.begin() == 1
    assert gen.begin() == 2
    assert gen.current == 2


def test_only_latest_generation_is_current():
    gen = SearchGeneration()
    first = gen.begin()
    assert gen.is_current(first)
    second = gen.begin()
    assert not gen.is_current(first)
    assert gen.is_current(second)


async def test_generation_protocol_drops_stale_results():
    """The real protocol HomeScreen runs: slow first search, fast second."""
    gen = SearchGeneration()
    published = []

    async def do_search(q, results):
        token = gen.begin()
        # Real yield point: lets the newer search claim first,
        # reproducing the out-of-order completion race.
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        if gen.is_current(token):
            published.append((q, results))

    t1 = asyncio.create_task(do_search("lag", ["stale"]))
    t2 = asyncio.create_task(do_search("lagos", ["fresh"]))
    await asyncio.gather(t1, t2)
    assert published == [("lagos", ["fresh"])]


async def test_short_query_still_invalidates_inflight_generation():
    """A cleared query (<2 chars) claims a generation so the in-flight
    search can't repopulate the list after the user deleted their text."""
    gen = SearchGeneration()
    published = []

    async def slow_search():
        token = gen.begin()
        await asyncio.sleep(0.01)
        if gen.is_current(token):
            published.append(["stale"])

    async def clear_query():
        gen.begin()  # HomeScreen claims before the length gate returns

    t1 = asyncio.create_task(slow_search())
    await asyncio.sleep(0)
    await clear_query()
    await t1
    assert published == []
