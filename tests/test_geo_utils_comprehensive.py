"""Geo utils edge cases."""

import pytest

from core.geo_utils import calculate_haversine_distance_km, format_distance


def test_antipodal():
    d = calculate_haversine_distance_km(0, 0, 0, 180)
    assert 19900 < d < 20100


@pytest.mark.parametrize(
    "km,expected_sub",
    [
        (0.0, "0 m"),
        (0.001, "1 m"),
        (0.999, "999 m"),
        (1.0, "1.0 km"),
        (99.9, "99.9 km"),
        (100.0, "100 km"),
        (1450.0, "1,450 km"),
        (12.4, "12.4 km"),
    ],
)
def test_format_boundaries(km, expected_sub):
    assert expected_sub in format_distance(km)
