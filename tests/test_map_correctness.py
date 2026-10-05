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
