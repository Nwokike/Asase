"""Adaptive navigation chrome regressions (Phase D1)."""

import flet as ft
from flet_tree import walk_texts

from components.adaptive_nav import (
    NAV_ITEMS,
    build_navigation_bar,
    build_navigation_rail,
    build_sidebar,
    build_status_bar,
    window_class,
)


def test_window_class_edges():
    assert window_class(None) == "compact"
    assert window_class(599) == "compact"
    assert window_class(600) == "medium"
    assert window_class(839) == "medium"
    assert window_class(840) == "expanded"
    assert window_class(1920) == "expanded"


def test_nav_items_cover_five_tabs():
    assert len(NAV_ITEMS) == 5
    assert [i[0] for i in NAV_ITEMS] == [0, 1, 2, 3, 4]


def test_navigation_bar_selects_tab():
    bar = build_navigation_bar(2, lambda e: None)
    assert isinstance(bar, ft.NavigationBar)
    assert bar.selected_index == 2
    assert len(bar.destinations) == 5


def test_navigation_rail_selects_tab():
    rail = build_navigation_rail(1, lambda e: None)
    assert isinstance(rail, ft.NavigationRail)
    assert rail.selected_index == 1
    assert len(rail.destinations) == 5


def test_sidebar_expanded_shows_labels():
    side = build_sidebar(0, lambda i: None, False, lambda: None)
    assert isinstance(side, ft.Container)
    assert side.width == 264.0
    texts = [t.value for t in walk_texts(side)]
    assert "Radar" in texts and "Settings" in texts


def test_sidebar_collapsed_hides_labels():
    side = build_sidebar(0, lambda i: None, True, lambda: None)
    assert side.width == 72.0
    texts = [t.value for t in walk_texts(side)]
    assert "Radar" not in texts


def test_sidebar_active_tab_highlighted():
    side = build_sidebar(3, lambda i: None, False, lambda: None)
    texts = [t.value for t in walk_texts(side)]
    assert "History" in texts


def test_status_bar_renders_context():
    bar = build_status_bar("Lagos", 3, "Kp 4.2", lambda: None)
    texts = [t.value for t in walk_texts(bar)]
    joined = " ".join(t or "" for t in texts)
    assert "Lagos" in joined
    assert "3 alerts" in joined
    assert "Kp 4.2" in joined


def test_status_bar_refresh_click_invokes_callback_without_warnings():
    """The status bar calls on_refresh as a plain sync callback — the
    app_shell wiring must pass a sync wrapper (schedule), never the bare
    async refresh_all (that produced 'coroutine never awaited' + no refresh)."""
    import warnings

    fired = []
    bar = build_status_bar(
        "Lagos", 3, "Kp 4.2", lambda: None, on_refresh=lambda: fired.append(1)
    )
    from flet_tree import walk

    refresh_btns = [
        b
        for b in walk(bar)
        if isinstance(b, ft.IconButton) and b.tooltip == "Sync Live Feeds"
    ]
    assert len(refresh_btns) == 1
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        refresh_btns[0].on_click(None)
    assert fired == [1]
    assert not [w for w in caught if issubclass(w.category, RuntimeWarning)]
