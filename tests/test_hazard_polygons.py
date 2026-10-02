"""EONET polygon preservation + rendering (Batch N)."""

import flet_map as fmap

from components.hazard_map import HazardMap, build_hazard_polygons
from models.disasters import EonetEvent


def _event(geom):
    return EonetEvent.model_validate(
        {
            "id": "E1",
            "title": "Perimeter Fire",
            "categories": [{"id": "wildfires", "title": "Wildfires"}],
            "geometry": [
                {"date": "2026-01-01", "type": "Polygon", "coordinates": geom}
            ],
        }
    )


def test_polygon_ring_preserved():
    ev = _event([[[-120.0, 37.0], [-119.0, 37.0], [-119.0, 38.0], [-120.0, 37.0]]])
    d = ev.to_map_dict()
    assert d["polygon_ring"] == [
        [-120.0, 37.0],
        [-119.0, 37.0],
        [-119.0, 38.0],
        [-120.0, 37.0],
    ]
    # Point fallback still present.
    assert (d["longitude"], d["latitude"]) == (-120.0, 37.0)


def test_point_geometry_yields_no_ring():
    ev = _event([-120.0, 37.5])
    d = ev.to_map_dict()
    assert d["polygon_ring"] is None


def test_degenerate_ring_yields_no_ring():
    ev = _event([[[-120.0, 37.0], [-119.0, 37.0]]])  # only 2 positions
    assert ev.to_map_dict()["polygon_ring"] is None


def test_build_hazard_polygons_renders_perimeters():
    ring = [[-120.0, 37.0], [-119.0, 37.0], [-119.0, 38.0], [-120.0, 37.0]]
    polys = build_hazard_polygons(
        [
            {"type": "wildfire", "title": "Fire", "polygon_ring": ring},
            {"type": "storm", "title": "No ring", "polygon_ring": None},
        ]
    )
    assert len(polys) == 1
    assert len(polys[0].coordinates) == 4
    assert polys[0].coordinates[0].latitude == 37.0
    assert polys[0].coordinates[0].longitude == -120.0


def test_hazard_map_includes_polygon_layer():
    ring = [[-120.0, 37.0], [-119.0, 37.0], [-119.0, 38.0], [-120.0, 37.0]]
    hmap = HazardMap(
        lat=0.0,
        lon=0.0,
        disasters=[
            {"type": "wildfire", "title": "Fire", "polygon_ring": ring},
        ],
    )
    from flet_tree import walk

    # walk() descends into Map.layers since the Batch S slot fix.
    layers = [c for c in walk(hmap) if isinstance(c, fmap.MapLayer)]
    assert any(isinstance(layer, fmap.PolygonLayer) for layer in layers)
