"""Open-Meteo Geocoding and Elevation client with Pydantic v2."""

from __future__ import annotations

import logging

from core.constants import OPEN_METEO_ELEVATION, OPEN_METEO_GEOCODING
from core.network import AUTOCOMPLETE_TIMEOUT, NetworkManager
from models.geocoding import GeocodingResponse

logger = logging.getLogger("asase.geocoding")


class GeocodingService:
    @staticmethod
    async def search_cities(query: str) -> list[dict]:
        """Search global locations by city name or keyword."""
        if not query or len(query.strip()) < 2:
            return []
        url = f"{OPEN_METEO_GEOCODING}?name={query.strip()}&count=10&language=en&format=json"
        try:
            client = NetworkManager.get_client()
            res = await client.get(url, timeout=AUTOCOMPLETE_TIMEOUT)
            if res.status_code == 200:
                resp = GeocodingResponse.model_validate_json(res.content)
                return [
                    {
                        "name": r.name,
                        "country": r.country,
                        "country_code": r.country_code,
                        "admin1": r.admin1,
                        "latitude": r.latitude,
                        "longitude": r.longitude,
                        "elevation": r.elevation or 0.0,
                        "timezone": r.timezone,
                        "population": r.population,
                    }
                    for r in resp.results
                ]
        except Exception as ex:
            logger.warning("Geocoding search failed for '%s': %s", query, ex)
        return []

    @staticmethod
    async def get_elevation(lat: float, lon: float) -> float:
        """Fetch terrain elevation (m) via Open-Meteo Elevation API."""
        url = f"{OPEN_METEO_ELEVATION}?latitude={lat}&longitude={lon}"
        try:
            client = NetworkManager.get_client()
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                elevations = data.get("elevation", [0.0])
                if elevations:
                    return float(elevations[0])
        except Exception as ex:
            logger.warning("Elevation lookup failed for (%s, %s): %s", lat, lon, ex)
        return 0.0
