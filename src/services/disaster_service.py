"""NASA EONET natural disaster client — now category-aware."""

from __future__ import annotations

import logging

from core.constants import EONET_CATEGORY_MAP, NASA_EONET_EVENTS
from core.validators import conditional_get_json
from models.disasters import EonetEvent, EonetResponse

logger = logging.getLogger("asase.disasters")


class DisasterService:
    @staticmethod
    async def fetch_active_disasters(category: str = "all") -> list[dict] | None:
        """Fetch open natural events, optionally filtered by category."""
        url = NASA_EONET_EVENTS
        cat_param = EONET_CATEGORY_MAP.get(category, "")
        if cat_param:
            url += f"&category={cat_param}"
        events: list[dict] = []
        try:
            status, payload = await conditional_get_json(url, log_name="NASA EONET")
            if status not in (200, 304):
                # Transport/HTTP failure: keep last-good data + stale stamp.
                return None
            if not isinstance(payload, dict):
                # Corrupt 200 (truncated body / HTML error page): keep
                # last-good data instead of blanking the feed.
                return None
            try:
                eonet = EonetResponse.model_validate(payload)
                raw_events = eonet.events
            except Exception:
                # One malformed event must not poison the batch —
                # validate per-event and keep the survivors.
                raw_events = []
                for raw in payload.get("events", []):
                    try:
                        raw_events.append(EonetEvent.model_validate(raw))
                    except Exception as ex:
                        logger.debug("EONET: skipping malformed event: %s", ex)
            for ev in raw_events:
                try:
                    coords = ev.primary_coordinates
                    if coords != (0.0, 0.0):
                        events.append(ev.to_map_dict())
                except Exception as ex:
                    logger.debug("EONET: skipping unrenderable event: %s", ex)
            logger.info(
                "NASA EONET (%s): %d events%s",
                category,
                len(events),
                " (cached 304)" if status == 304 else "",
            )
        except Exception as ex:
            logger.warning("NASA EONET fetch failed: %s", ex)
            return None
        return events
