"""USGS Earthquake Hazards Program client (100% Free & No-Auth)."""

from __future__ import annotations

import datetime
import logging

import httpx

from core.constants import (
    USGS_EARTHQUAKES_DAY,
    USGS_EARTHQUAKES_SIGNIFICANT,
)

logger = logging.getLogger("asase.seismic")


class SeismicService:
    @staticmethod
    async def fetch_earthquakes(min_magnitude: float = 2.5) -> list[dict]:
        """Fetch live global earthquakes from USGS GeoJSON feed."""
        url = (
            USGS_EARTHQUAKES_DAY
            if min_magnitude <= 4.0
            else USGS_EARTHQUAKES_SIGNIFICANT
        )
        events: list[dict] = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    features = data.get("features", [])
                    for f in features:
                        props = f.get("properties", {})
                        geom = f.get("geometry", {})
                        coords = geom.get("coordinates", [0.0, 0.0, 0.0])
                        mag = float(props.get("mag") or 0.0)

                        if mag < min_magnitude:
                            continue

                        timestamp_ms = props.get("time") or 0
                        time_str = datetime.datetime.fromtimestamp(
                            timestamp_ms / 1000.0, tz=datetime.UTC
                        ).strftime("%Y-%m-%d %H:%M UTC")

                        events.append(
                            {
                                "id": f.get("id", ""),
                                "title": props.get("title", "Earthquake"),
                                "place": props.get("place", "Unknown location"),
                                "magnitude": mag,
                                "depth_km": float(coords[2])
                                if len(coords) > 2
                                else 0.0,
                                "longitude": float(coords[0]),
                                "latitude": float(coords[1]),
                                "tsunami": bool(props.get("tsunami", 0)),
                                "alert": props.get("alert") or "green",
                                "mmi": props.get("mmi") or 0.0,
                                "time_str": time_str,
                                "url": props.get("url", ""),
                                "type": "earthquake",
                            }
                        )
                    logger.info(
                        "USGS: Loaded %d seismic events (min M%.1f)",
                        len(events),
                        min_magnitude,
                    )
        except Exception as ex:
            logger.warning("USGS Earthquake fetch failed: %s", ex)
        return events
