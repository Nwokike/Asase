"""Map correctness regressions (Batch H).

- No fallback_url (it disables all in-memory tile caching).
- Attribution credits OSM; UA follows the recommended shape.
- Overflow past the marker caps surfaces a "+N more" chip.
"""

import flet as ft
import flet_map as fmap
from flet_tree import walk, walk_texts

from components.hazard_map import (
    _MAX_QUAKE_MARKERS,
    _TILE_ATTRIBUTION,
    _TILE_USER_AGENT,
    HazardMap,
)


def _eq(i):
    return {
        "id": f"eq{i}",
        "latitude": 10.0,
        "longitude": 20.0,
        "magnitude": 5.0,
        "type": "earthquake",
    }


def _tile_layers(root):
    # walk() descends into Map.layers since the Batch S slot fix.
    return [c for c in walk(root) if isinstance(c, fmap.TileLayer)]


def test_tile_layer_has_no_fallback_url():
    hmap = HazardMap(lat=0.0, lon=0.0, earthquakes=[_eq(0)])
    layers = _tile_layers(hmap)
    assert len(layers) == 1
    assert layers[0].fallback_url in (None, "")


def test_tile_user_agent_follows_recommended_shape():
    assert "/" in _TILE_USER_AGENT and "(+" in _TILE_USER_AGENT
    assert _TILE_USER_AGENT != "ng.kiri.asase"


def test_attribution_credits_osm():
    assert "OpenStreetMap" in _TILE_ATTRIBUTION
    for name in ("Esri", "USGS", "NASA", "NOAA"):
        assert name in _TILE_ATTRIBUTION


def test_overflow_chip_surfaces_truncation():
    quakes = [_eq(i) for i in range(_MAX_QUAKE_MARKERS + 25)]
    hmap = HazardMap(lat=0.0, lon=0.0, earthquakes=quakes)
    assert isinstance(hmap, ft.Stack)
    texts = [t.value for t in walk_texts(hmap)]
    assert any("+25 more" in (t or "") for t in texts)


def test_no_overflow_chip_within_caps():
    hmap = HazardMap(lat=0.0, lon=0.0, earthquakes=[_eq(0)])
    assert isinstance(hmap, ft.Stack)  # map body + zoom pill, no chip
    texts = [t.value for t in walk_texts(hmap)]
    assert not any("more" in (t or "") for t in texts)


def test_markers_have_no_rotate_noop():
    # rotate=None inherits MarkerLayer.rotate (default False); either way
    # no per-marker counter-rotation cost is requested.
    from components.hazard_map import build_hazard_marker

    marker = build_hazard_marker(_eq(0))
    assert marker.rotate in (None, False)


def test_desktop_zoom_controls_present():
    """The +/− zoom pill ships on every HazardMap (desktop users have no
    pinch gesture; wheel zoom alone was undiscoverable)."""
    hmap = HazardMap(lat=0.0, lon=0.0, earthquakes=[])
    tooltips = [b.tooltip for b in walk(hmap) if isinstance(b, ft.IconButton)]
    assert "Zoom in" in tooltips
    assert "Zoom out" in tooltips


def test_zoom_click_schedules_map_methods():
    """Clicking +/− schedules the ref'd Map's zoom_in/zoom_out through
    core.tasks.schedule — never a bare coroutine call."""
    from unittest.mock import patch

    class _FakeMap:
        def __init__(self):
            self.calls = []

        async def zoom_in(self):
            self.calls.append("in")

        async def zoom_out(self):
            self.calls.append("out")

    class _Ref:
        current = _FakeMap()

    hmap = HazardMap(lat=0.0, lon=0.0, earthquakes=[], map_ref=_Ref())
    buttons = {
        b.tooltip: b
        for b in walk(hmap)
        if isinstance(b, ft.IconButton) and b.tooltip in ("Zoom in", "Zoom out")
    }
    scheduled = []
    with patch(
        "components.hazard_map.schedule",
        side_effect=lambda fn, **kw: scheduled.append(fn),
    ):
        buttons["Zoom in"].on_click(None)
        buttons["Zoom out"].on_click(None)
    assert [f.__name__ for f in scheduled] == ["zoom_in", "zoom_out"]
    # Coroutine functions bound to the ref'd Map control (Flet's ref=
    # wiring sets ref.current to the created Map; schedule must receive
    # real async callables, never bare-invoked coroutines).
    import inspect

    assert all(inspect.iscoroutinefunction(f) for f in scheduled)
    assert all(isinstance(f.__self__, fmap.Map) for f in scheduled)


def test_zoom_click_without_map_ref_is_noop():
    hmap = HazardMap(lat=0.0, lon=0.0, earthquakes=[], map_ref=None)
    buttons = [
        b for b in walk(hmap) if isinstance(b, ft.IconButton) and b.tooltip == "Zoom in"
    ]
    assert len(buttons) == 1
    buttons[0].on_click(None)  # must not raise


def _zoom_pill(root):
    """The vertical zoom pill container inside a map tree (or [])."""
    return [
        c
        for c in walk(root)
        if isinstance(c, ft.Container)
        and isinstance(c.content, ft.Column)
        and any(
            isinstance(b, ft.IconButton) and b.tooltip == "Zoom in"
            for b in c.content.controls
        )
    ]


def test_zoom_pill_placement_per_embed():
    from components.hazard_map import HazardMap

    # Default (full map screen + compact mini-map): top-left pill — corner
    # is free there (layer stack is top-right, sheet/panels are bottom).
    hmap = HazardMap(lat=0.0, lon=0.0, earthquakes=[])
    pill = _zoom_pill(hmap)
    assert len(pill) == 1
    assert pill[0].top is not None and pill[0].left is not None  # positioned top-left

    # Home canvas: NO floating pill — the inter-panel gap is only 8px on
    # medium, so the home drops its own in-rail zoom row instead.
    hmap2 = HazardMap(lat=0.0, lon=0.0, earthquakes=[], zoom_placement="none")
    assert _zoom_pill(hmap2) == []


def test_rail_zoom_is_the_same_pill_design():
    """Home's zoom control is the SAME pill as the full map's — only its
    position changes (it docks at the rail's bottom-left instead of the
    map's top-left)."""
    from components.hazard_map import build_zoom_controls

    class _Ref:
        pass

    pill = build_zoom_controls(_Ref())
    # Vertical pill: Column of icons inside a 40px-wide glass container —
    # identical structure to the map-screen pill.
    assert isinstance(pill, ft.Container)
    assert isinstance(pill.content, ft.Column)
    assert pill.width == 40
    tooltips = [b.tooltip for b in walk(pill) if isinstance(b, ft.IconButton)]
    assert tooltips == ["Zoom in", "Zoom out"]  # plus over minus


def test_rail_zoom_click_schedules_map_methods():
    from unittest.mock import patch

    from components.hazard_map import build_zoom_controls

    class _FakeMap:
        async def zoom_in(self):
            pass

        async def zoom_out(self):
            pass

    ref = type("R", (), {"current": _FakeMap()})()
    pill = build_zoom_controls(ref)
    buttons = {b.tooltip: b for b in walk(pill) if isinstance(b, ft.IconButton)}
    scheduled = []
    with patch(
        "components.hazard_map.schedule",
        side_effect=lambda fn, **kw: scheduled.append(fn),
    ):
        buttons["Zoom out"].on_click(None)
        buttons["Zoom in"].on_click(None)
    assert [f.__name__ for f in scheduled] == ["zoom_out", "zoom_in"]
