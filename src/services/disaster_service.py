"""NASA EONET (Earth Observatory Natural Event Tracker) & Disaster Client."""

from __future__ import annotations

import logging

import httpx

from core.constants import NASA_EONET_EVENTS

logger = logging.getLogger("asase.disasters")


class DisasterService:
    @staticmethod
    async def fetch_active_disasters() -> list[dict]:
        """Fetch open natural events (wildfires, volcanoes, severe storms) from NASA EONET."""
        events: list[dict] = []
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.get(NASA_EONET_EVENTS)
                if res.status_code == 200:
                    data = res.json()
                    raw_events = data.get("events", [])
                    for ev in raw_events:
                        categories = ev.get("categories", [])
                        cat_id = (
                            categories[0].get("id", "hazard")
                            if categories
                            else "hazard"
                        )
                        cat_title = (
                            categories[0].get("title", "Natural Event")
                            if categories
                            else "Natural Event"
                        )

                        # Extract geometry
                        geometry = ev.get("geometry", [])
                        if not geometry:
                            continue
                        latest_geom = geometry[-1]
                        coords = latest_geom.get("coordinates", [0.0, 0.0])
                        if not coords or len(coords) < 2:
                            continue

                        # Handle point vs polygon
                        lon = (
                            float(coords[0])
                            if isinstance(coords[0], (int, float))
                            else float(coords[0][0])
                        )
                        lat = (
                            float(coords[1])
                            if isinstance(coords[1], (int, float))
                            else float(coords[0][1])
                        )

                        events.append(
                            {
                                "id": ev.get("id", ""),
                                "title": ev.get("title", "Natural Event"),
                                "category_id": cat_id,
                                "category_title": cat_title,
                                "date": latest_geom.get("date", ""),
                                "longitude": lon,
                                "latitude": lat,
                                "url": ev.get("link", ""),
                                "type": "wildfire"
                                if "fire" in cat_id.lower()
                                else (
                                    "storm" if "storm" in cat_id.lower() else "disaster"
                                ),
                            }
                        )
                    logger.info(
                        "NASA EONET: Loaded %d active disaster events", len(events)
                    )
        except Exception as ex:
            logger.warning("NASA EONET fetch failed: %s", ex)
        return events
