"""Open-Meteo Geocoding and Elevation client with Pydantic v2."""

from __future__ import annotations

import logging

from core.constants import (
    BIGDATACLOUD_REVERSE_GEOCODING,
    OPEN_METEO_ELEVATION,
    OPEN_METEO_GEOCODING,
    OPEN_METEO_REVERSE_GEOCODING,
)
from core.network import AUTOCOMPLETE_TIMEOUT, NetworkManager
from models.geocoding import GeocodingResponse

logger = logging.getLogger("asase.geocoding")


_GEOCODE_LRU: dict[str, list[dict]] = {}
_GEOCODE_LRU_MAX = 20
_REVERSE_GEOCODE_LRU: dict[str, dict] = {}
_REVERSE_GEOCODE_LRU_MAX = 30


class GeocodingService:
    @staticmethod
    async def search_cities(query: str) -> list[dict]:
        """Search global locations by city name or keyword — with in-memory LRU cache."""
        q = query.strip().lower()
        if len(q) < 2:
            return []
        if q in _GEOCODE_LRU:
            # Deep-ish copy: callers mutate result dicts in place, and a
            # shallow list() would still share the inner dicts.
            return [dict(r) for r in _GEOCODE_LRU[q]]
        url = OPEN_METEO_GEOCODING
        params = {"name": q, "count": 10, "language": "en", "format": "json"}
        try:
            client = NetworkManager.get_client()
            res = await client.get(url, params=params, timeout=AUTOCOMPLETE_TIMEOUT)
            if res.status_code == 200:
                resp = GeocodingResponse.model_validate_json(res.content)
                out = [
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
                if len(_GEOCODE_LRU) >= _GEOCODE_LRU_MAX:
                    _GEOCODE_LRU.pop(next(iter(_GEOCODE_LRU)))
                _GEOCODE_LRU[q] = out
                return [dict(r) for r in out]
            else:
                logger.warning(
                    "Geocoding search: HTTP %d for '%s'", res.status_code, query
                )
        except Exception as ex:
            logger.warning("Geocoding search failed for '%s': %s", query, ex)
        return []

    @staticmethod
    async def reverse_geocode(lat: float, lon: float) -> dict | None:
        """Resolve (lat, lon) coordinates to nearest city and country name.

        Tries Open-Meteo reverse geocoding first, falling back to BigDataCloud
        client-side reverse geocoding. Both are completely auth-free.
        """
        cache_key = f"{lat:.3f},{lon:.3f}"
        if cache_key in _REVERSE_GEOCODE_LRU:
            # Copy: callers must not mutate the cached dict.
            return dict(_REVERSE_GEOCODE_LRU[cache_key])

        client = NetworkManager.get_client()

        # 1. Primary: Open-Meteo Reverse Geocoding
        url_om = OPEN_METEO_REVERSE_GEOCODING
        params_om = {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "language": "en",
            "format": "json",
        }
        try:
            res = await client.get(
                url_om, params=params_om, timeout=AUTOCOMPLETE_TIMEOUT
            )
            if res.status_code == 200:
                resp = GeocodingResponse.model_validate_json(res.content)
                if resp.results:
                    r = resp.results[0]
                    result = {
                        "name": r.name,
                        "country": r.country,
                        "country_code": r.country_code,
                        "admin1": r.admin1,
                        "latitude": r.latitude,
                        "longitude": r.longitude,
                        "elevation": r.elevation or 0.0,
                    }
                    if len(_REVERSE_GEOCODE_LRU) >= _REVERSE_GEOCODE_LRU_MAX:
                        _REVERSE_GEOCODE_LRU.pop(next(iter(_REVERSE_GEOCODE_LRU)))
                    _REVERSE_GEOCODE_LRU[cache_key] = result
                    return dict(result)
        except Exception as ex:
            logger.debug(
                "Open-Meteo reverse geocoding missed for (%s, %s): %s", lat, lon, ex
            )

        # 2. Fallback: BigDataCloud Free Client Reverse Geocoding
        url_bdc = BIGDATACLOUD_REVERSE_GEOCODING
        params_bdc = {
            "latitude": f"{lat:.4f}",
            "longitude": f"{lon:.4f}",
            "localityLanguage": "en",
        }
        try:
            res = await client.get(
                url_bdc, params=params_bdc, timeout=AUTOCOMPLETE_TIMEOUT
            )
            if res.status_code == 200:
                data = res.json()
                city = (
                    data.get("city")
                    or data.get("locality")
                    or data.get("principalSubdivision")
                    or f"Coord ({lat:.2f}, {lon:.2f})"
                )
                country = data.get("countryName") or ""
                result = {
                    "name": city,
                    "country": country,
                    "country_code": data.get("countryCode", ""),
                    "admin1": data.get("principalSubdivision", ""),
                    "latitude": lat,
                    "longitude": lon,
                    "elevation": 0.0,
                }
                if len(_REVERSE_GEOCODE_LRU) >= _REVERSE_GEOCODE_LRU_MAX:
                    _REVERSE_GEOCODE_LRU.pop(next(iter(_REVERSE_GEOCODE_LRU)))
                _REVERSE_GEOCODE_LRU[cache_key] = result
                return dict(result)
        except Exception as ex:
            logger.debug(
                "BigDataCloud reverse geocoding missed for (%s, %s): %s", lat, lon, ex
            )

        return None

    @staticmethod
    async def get_elevation(lat: float, lon: float) -> float | None:
        """Terrain elevation (m) via Open-Meteo Elevation API.

        Returns None on failure — 0.0 is genuine sea level, so failure and
        sea level must be distinguishable for the controller to assign.
        """
        url = OPEN_METEO_ELEVATION
        params = {"latitude": lat, "longitude": lon}
        try:
            client = NetworkManager.get_client()
            res = await client.get(url, params=params, timeout=AUTOCOMPLETE_TIMEOUT)
            if res.status_code == 200:
                data = res.json()
                elevations = data.get("elevation", [0.0])
                if elevations:
                    return float(elevations[0])
        except Exception as ex:
            logger.warning("Elevation lookup failed for (%s, %s): %s", lat, lon, ex)
        return None
