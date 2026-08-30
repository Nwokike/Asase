"""use_map_center — keep a flet-map Map ref centered on the active focus point.

The Map control only honors `initial_center` at creation, so a kept-alive map
never moves when the user picks a new location. This hook watches
(lat, lon, zoom) and calls the control's async `center_on(...)` with an
animation whenever the focus point actually changes.
"""

from __future__ import annotations

import asyncio
import logging

import flet as ft

logger = logging.getLogger("asase.hooks.map_center")


def use_map_center(map_ref, lat: float, lon: float, zoom: float):
    """Animate `map_ref.current` to (lat, lon) whenever the focus point changes.

    Args:
        map_ref: ft.Ref that will hold the map.Map control.
        lat: Latitude of the new focus point.
        lon: Longitude of the new focus point.
        zoom: Zoom level to apply when re-centering.
    """

    async def _center():
        m = map_ref.current
        if m is None:
            return
        try:
            import flet_map as fmap

            await m.center_on(
                point=fmap.MapLatitudeLongitude(lat, lon),
                zoom=zoom,
                cancel_ongoing_animations=True,
            )
        except Exception as ex:
            logger.debug("Map re-center skipped: %s", ex)

    def _schedule():
        if (lat, lon) != (0.0, 0.0):
            asyncio.create_task(_center())

    ft.use_effect(_schedule, [lat, lon])
