"""NASA EONET & GDACS Natural Disaster Client with Pydantic v2."""

from __future__ import annotations

import logging

from core.constants import NASA_EONET_EVENTS
from core.network import NetworkManager
from models.disasters import EonetResponse

logger = logging.getLogger("asase.disasters")


class DisasterService:
    @staticmethod
    async def fetch_active_disasters() -> list[dict]:
        """Fetch open natural events (wildfires, volcanoes, severe storms) from NASA EONET v3."""
        events: list[dict] = []
        try:
            client = NetworkManager.get_client()
            res = await client.get(NASA_EONET_EVENTS)
            if res.status_code == 200:
                eonet = EonetResponse.model_validate_json(res.content)
                for ev in eonet.events:
                    coords = ev.primary_coordinates
                    if coords != (0.0, 0.0):
                        events.append(ev.to_map_dict())
                logger.info(
                    "NASA EONET: Validated %d active disaster events", len(events)
                )
        except Exception as ex:
            logger.warning("NASA EONET fetch failed: %s", ex)
        return events
