"""Search race + spinner regressions (Batch I).

The generation counter lives inside the HomeScreen closure, so these tests
verify the contract at the builder level (spinner param) plus a faithful
simulation of the generation protocol.
"""

import flet as ft

from components.home.location_search_bar import build_location_search_bar


def _bar(**kwargs):
    import logging

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


def test_generation_protocol_drops_stale_results():
    """Faithful simulation of the home_screen generation counter."""
    published = []
    is_searching = False
    generation = 0

    async def do_search(q, results):
        nonlocal is_searching, generation
        generation += 1
        mine = generation
        is_searching = True
        # Real yield point: lets the newer search increment first,
        # reproducing the out-of-order completion race.
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        if mine == generation:
            published.append((q, results))
            is_searching = False

    import asyncio

    async def scenario():
        # Slow first search, fast second search: only second publishes.
        t1 = asyncio.create_task(do_search("lag", ["stale"]))
        t2 = asyncio.create_task(do_search("lagos", ["fresh"]))
        await asyncio.gather(t1, t2)

    asyncio.run(scenario())
    assert published == [("lagos", ["fresh"])]
    assert is_searching is False
