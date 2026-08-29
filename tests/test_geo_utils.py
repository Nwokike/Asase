"""Tests for geodesic distance calculation and formatting."""

from core.geo_utils import calculate_haversine_distance_km, format_distance


def test_haversine_distance_zero():
    # Same point
    d = calculate_haversine_distance_km(6.5244, 3.3792, 6.5244, 3.3792)
    assert d == 0.0


def test_haversine_distance_london_to_paris():
    # London (51.5074, -0.1278) to Paris (48.8566, 2.3522) ~ 343 km
    d = calculate_haversine_distance_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert 330.0 < d < 360.0


def test_format_distance_meters():
    assert format_distance(0.45) == "450 m away"


def test_format_distance_kilometers():
    assert format_distance(12.4) == "12.4 km away"
    assert format_distance(1450.0) == "1,450 km away"
