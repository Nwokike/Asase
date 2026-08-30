"""NASA EONET natural disaster client — now category-aware."""

from __future__ import annotations

import logging

from core.constants import EONET_CATEGORY_MAP, NASA_EONET_EVENTS
from core.network import NetworkManager
from models.disasters import EonetResponse

logger = logging.getLogger("asase.disasters")


class DisasterService:
    @staticmethod
    async def fetch_active_disasters(category: str = "all") -> list[dict]:
        """Fetch open natural events, optionally filtered by category."""
        url = NASA_EONET_EVENTS
        cat_param = EONET_CATEGORY_MAP.get(category, "")
        if cat_param:
            url += f"&category={cat_param}"
        events: list[dict] = []
        try:
            client = NetworkManager.get_client()
            res = await client.get(url)
            if res.status_code == 200:
                eonet = EonetResponse.model_validate_json(res.content)
                for ev in eonet.events:
                    coords = ev.primary_coordinates
                    if coords != (0.0, 0.0):
                        events.append(ev.to_map_dict())
                logger.info("NASA EONET (%s): %d events", category, len(events))
        except Exception as ex:
            logger.warning("NASA EONET fetch failed: %s", ex)
        return events
