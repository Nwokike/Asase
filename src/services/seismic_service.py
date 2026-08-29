"""USGS Earthquake Hazards Program client with FDSN and GeoJSON stream support."""

from __future__ import annotations

import logging

from core.constants import (
    USGS_EARTHQUAKES_DAY,
    USGS_EARTHQUAKES_SIGNIFICANT,
)
from core.network import NetworkManager
from models.seismic import EarthquakeFeatureCollection

logger = logging.getLogger("asase.seismic")


class SeismicService:
    @staticmethod
    async def fetch_earthquakes(min_magnitude: float = 2.5) -> list[dict]:
        """Fetch live global earthquakes using connection-pooled HTTPX client & Pydantic v2."""
        url = (
            USGS_EARTHQUAKES_DAY
            if min_magnitude <= 4.0
            else USGS_EARTHQUAKES_SIGNIFICANT
        )
        events: list[dict] = []
        try:
            client = NetworkManager.get_client()
            res = await client.get(url)
            if res.status_code == 200:
                # Fast zero-copy Rust-accelerated parsing
                collection = EarthquakeFeatureCollection.model_validate_json(
                    res.content
                )
                for feat in collection.features:
                    if feat.properties.mag >= min_magnitude:
                        events.append(feat.to_map_dict())
                logger.info(
                    "USGS: Validated %d seismic events (min M%.1f)",
                    len(events),
                    min_magnitude,
                )
        except Exception as ex:
            logger.warning("USGS Earthquake fetch failed: %s", ex)
        return events

    @staticmethod
    async def fetch_radius_history(
        lat: float, lon: float, radius_km: float = 500.0, min_magnitude: float = 3.0
    ) -> list[dict]:
        """Fetch local earthquake history within radius using USGS FDSN Web Services."""
        url = (
            f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
            f"&latitude={lat}&longitude={lon}&maxradiuskm={radius_km}"
            f"&minmagnitude={min_magnitude}&orderby=time&limit=50"
        )
        events: list[dict] = []
        try:
            client = NetworkManager.get_client()
            res = await client.get(url)
            if res.status_code == 200:
                collection = EarthquakeFeatureCollection.model_validate_json(
                    res.content
                )
                events = [feat.to_map_dict() for feat in collection.features]
                logger.info(
                    "USGS FDSN: Found %d historical events within %d km",
                    len(events),
                    int(radius_km),
                )
        except Exception as ex:
            logger.warning("USGS FDSN radial query failed: %s", ex)
        return events
