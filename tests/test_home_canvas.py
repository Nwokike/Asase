"""Home canvas layout-branch regressions (D2 Batch 2).

Behavioral: exercises the REAL panel-width computation the HomeScreen
layout branch runs (canvas_panel_widths), not source-text markers.
"""

from core import tokens
from screens.home_screen import canvas_panel_widths


def test_window_class_boundaries():
    from components.adaptive_nav import window_class

    assert window_class(400) == "compact"
    assert window_class(700) == "medium"
    assert window_class(1200) == "expanded"


def test_compact_keeps_scroll_layout_no_canvas():
    use_canvas, rail_w, feeds_w = canvas_panel_widths(400)
    assert use_canvas is False
    # Compact renders the single-column scroll; the panel sizes are inert.
    assert (rail_w, feeds_w) == (360.0, 420.0)


def test_medium_canvas_panels_fit_viewport():
    use_canvas, rail_w, feeds_w = canvas_panel_widths(700)
    assert use_canvas is True
    assert rail_w == min(320.0, 700 * 0.45)  # 315.0 — proportional, capped
    # Panels + their margins must not overflow the viewport: the map
    # canvas stays visible behind them.
    assert rail_w + feeds_w + 2 * tokens.SPACE_MD + 8 <= 700
    assert feeds_w >= 260.0


def test_medium_lower_boundary_panels_fit():
    use_canvas, rail_w, feeds_w = canvas_panel_widths(600)
    assert use_canvas is True
    assert rail_w + feeds_w + 2 * tokens.SPACE_MD + 8 <= 600
    assert rail_w <= 320.0
    assert feeds_w >= 260.0


def test_medium_wide_end_caps_rail_at_320():
    # 839.0 is the top of the medium band (WINDOW_MEDIUM_MAX).
    use_canvas, rail_w, _ = canvas_panel_widths(839)
    assert use_canvas is True
    assert rail_w == 320.0  # min(320, 839*0.45≈377) → cap


def test_expanded_canvas_panels_are_proportional_with_caps():
    # Roomier panels on big screens (the old fixed 360/420 cramped the
    # search rail + filter chips), capped so a 4K viewport can't drift.
    use_canvas, rail_w, feeds_w = canvas_panel_widths(1440)
    assert use_canvas is True
    assert rail_w == 1440 * 0.26
    assert feeds_w == 1440 * 0.34
    _, rail_4k, feeds_4k = canvas_panel_widths(2560)
    assert (rail_4k, feeds_4k) == (440.0, 560.0)
    # Small expanded window still gets sane minimums
    _, rail_mid, feeds_mid = canvas_panel_widths(850)
    assert (rail_mid, feeds_mid) == (360.0, 420.0)


def test_unknown_width_defaults_to_compact_scroll():
    use_canvas, _, _ = canvas_panel_widths(0)
    assert use_canvas is False
    use_canvas_none, _, _ = canvas_panel_widths(None)
    assert use_canvas_none is False


def test_filter_chips_wrap_and_all_visible():
    """All six hazard chips render and wrap — no horizontal scroller
    hiding Storm/Volcano behind a swipe."""
    import flet as ft
    from flet_tree import walk

    from components.home.hazard_filter_chips import build_hazard_filter_chips

    row = build_hazard_filter_chips(page=None, selected="all", on_select=lambda k: None)
    chips = [
        c
        for c in walk(row)
        if isinstance(c, ft.Container) and getattr(c, "on_click", None)
    ]
    labels = []
    for c in chips:
        texts = [t.value for t in walk(c) if isinstance(t, ft.Text)]
        labels.extend(t for t in texts if t)
    assert labels == ["All", "Seismic", "Wildfire", "Flood", "Storm", "Volcano"]
    # Wrapped content: the chips Row must carry wrap=True (no scroll)
    rows = [c for c in walk(row) if isinstance(c, ft.Row) and c.wrap is True]
    assert len(rows) == 1
    assert rows[0].wrap is True
