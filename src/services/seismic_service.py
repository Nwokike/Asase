"""USGS Earthquake Hazards Program client with FDSN and GeoJSON stream support."""

from __future__ import annotations

import logging

from core.constants import (
    USGS_EARTHQUAKES_DAY,
    USGS_EARTHQUAKES_SIGNIFICANT,
)
from core.validators import conditional_get_json
from models.seismic import EarthquakeFeature, EarthquakeFeatureCollection

logger = logging.getLogger("asase.seismic")


def _parse_features(raw_features: list) -> list[EarthquakeFeature]:
    """Validate features one at a time so a single malformed record
    cannot poison the whole batch — skip it and keep the rest."""
    parsed: list[EarthquakeFeature] = []
    for raw in raw_features:
        try:
            parsed.append(EarthquakeFeature.model_validate(raw))
        except Exception as ex:
            logger.debug("USGS: skipping malformed feature: %s", ex)
    return parsed


class SeismicService:
    @staticmethod
    async def fetch_earthquakes(min_magnitude: float = 2.5) -> list[dict] | None:
        """Fetch live global earthquakes using connection-pooled HTTPX client & Pydantic v2."""
        url = (
            USGS_EARTHQUAKES_DAY
            if min_magnitude <= 4.0
            else USGS_EARTHQUAKES_SIGNIFICANT
        )
        events: list[dict] = []
        try:
            status, payload = await conditional_get_json(url, log_name="USGS")
            if status not in (200, 304):
                # Transport/HTTP failure: distinguishable from an empty feed
                # so the controller keeps last-good data + stale timestamps.
                return None
            if status in (200, 304) and isinstance(payload, dict):
                try:
                    # Fast path: whole-collection Rust-accelerated parse.
                    collection = EarthquakeFeatureCollection.model_validate(payload)
                    features = collection.features
                except Exception:
                    # Slow path: one malformed record must not poison the
                    # batch — validate per-feature and keep the survivors.
                    raw = payload.get("features", [])
                    features = _parse_features(raw)
                for feat in features:
                    try:
                        if feat.properties.mag >= min_magnitude:
                            events.append(feat.to_map_dict())
                    except Exception as ex:
                        logger.debug("USGS: skipping unrenderable event: %s", ex)
                logger.info(
                    "USGS: Validated %d seismic events (min M%.1f)%s",
                    len(events),
                    min_magnitude,
                    " (cached 304)" if status == 304 else "",
                )
        except Exception as ex:
            logger.warning("USGS Earthquake fetch failed: %s", ex)
            return None
        return events

    @staticmethod
    async def fetch_radius_history(
        lat: float, lon: float, radius_km: float = 500.0, min_magnitude: float = 3.0
    ) -> list[dict] | None:
        """Fetch local earthquake history within radius using USGS FDSN Web Services."""
        url = (
            f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
            f"&latitude={lat}&longitude={lon}&maxradiuskm={radius_km}"
            f"&minmagnitude={min_magnitude}&orderby=time&limit=50"
        )
        events: list[dict] = []
        try:
            status, payload = await conditional_get_json(url, log_name="USGS FDSN")
            if status not in (200, 304):
                return None
            if status in (200, 304) and isinstance(payload, dict):
                try:
                    collection = EarthquakeFeatureCollection.model_validate(payload)
                    features = collection.features
                except Exception:
                    raw = payload.get("features", [])
                    features = _parse_features(raw)
                for feat in features:
                    try:
                        events.append(feat.to_map_dict())
                    except Exception as ex:
                        logger.debug("USGS FDSN: skipping unrenderable event: %s", ex)
                logger.info(
                    "USGS FDSN: Found %d historical events within %d km%s",
                    len(events),
                    int(radius_km),
                    " (cached 304)" if status == 304 else "",
                )
        except Exception as ex:
            logger.warning("USGS FDSN radial query failed: %s", ex)
            return None
        return events
