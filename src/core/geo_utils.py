"""Geodesic distance and proximity utilities for planetary hazards."""

from __future__ import annotations

import math


def calculate_haversine_distance_km(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculates the great-circle distance between two points in kilometers using the Haversine formula."""
    r = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


def format_distance(distance_km: float) -> str:
    """Formats distance for user display."""
    if distance_km < 1.0:
        return f"{int(distance_km * 1000)} m away"
    if distance_km < 100.0:
        return f"{distance_km:.1f} km away"
    return f"{round(distance_km):,} km away"
