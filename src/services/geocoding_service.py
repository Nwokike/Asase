"""Open-Meteo Geocoding and Elevation client (100% Free & No-Auth)."""

from __future__ import annotations

import logging

import httpx

from core.constants import OPEN_METEO_ELEVATION, OPEN_METEO_GEOCODING

logger = logging.getLogger("asase.geocoding")


class GeocodingService:
    @staticmethod
    async def search_cities(query: str) -> list[dict]:
        """Search global locations by city name or keyword."""
        if not query or len(query.strip()) < 2:
            return []
        url = f"{OPEN_METEO_GEOCODING}?name={query.strip()}&count=10&language=en&format=json"
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    return [
                        {
                            "name": r.get("name", ""),
                            "country": r.get("country", ""),
                            "country_code": r.get("country_code", ""),
                            "admin1": r.get("admin1", ""),
                            "latitude": float(r.get("latitude", 0.0)),
                            "longitude": float(r.get("longitude", 0.0)),
                            "elevation": float(r.get("elevation", 0.0)),
                            "timezone": r.get("timezone", "UTC"),
                            "population": r.get("population", 0),
                        }
                        for r in results
                    ]
        except Exception as ex:
            logger.warning("Geocoding search failed for '%s': %s", query, ex)
        return []

    @staticmethod
    async def get_elevation(lat: float, lon: float) -> float:
        """Fetch terrain elevation (m) via Open-Meteo Elevation API."""
        url = f"{OPEN_METEO_ELEVATION}?latitude={lat}&longitude={lon}"
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    elevations = data.get("elevation", [0.0])
                    if elevations:
                        return float(elevations[0])
        except Exception as ex:
            logger.warning("Elevation lookup failed for (%s, %s): %s", lat, lon, ex)
        return 0.0
