"""NOAA Space Weather Prediction Center (SWPC) client (100% Free & No-Auth)."""

from __future__ import annotations

import logging

import httpx

from core.constants import NOAA_SWPC_KP_INDEX, NOAA_SWPC_SOLAR_FLARES

logger = logging.getLogger("asase.space_weather")


class SpaceWeatherService:
    @staticmethod
    async def fetch_space_weather() -> dict:
        """Fetch real-time geomagnetic storm Kp-index and solar activity."""
        data = {
            "kp_index": 0.0,
            "geomagnetic_status": "Quiet",
            "solar_activity": "Normal",
            "raw_kp": [],
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                res = await client.get(NOAA_SWPC_KP_INDEX)
                if res.status_code == 200:
                    kp_data = res.json()
                    if isinstance(kp_data, list) and len(kp_data) > 1:
                        # Latest reading
                        latest = kp_data[-1]
                        kp_val = float(latest[1]) if len(latest) > 1 else 0.0
                        data["kp_index"] = kp_val
                        data["raw_kp"] = kp_data[-12:]  # Last 12 readings

                        if kp_val < 3.0:
                            data["geomagnetic_status"] = "Quiet (Normal)"
                        elif kp_val < 5.0:
                            data["geomagnetic_status"] = "Unsettled / Active"
                        elif kp_val < 6.0:
                            data["geomagnetic_status"] = "G1 Minor Geomagnetic Storm"
                        elif kp_val < 7.0:
                            data["geomagnetic_status"] = "G2 Moderate Geomagnetic Storm"
                        elif kp_val < 8.0:
                            data["geomagnetic_status"] = "G3 Strong Geomagnetic Storm"
                        else:
                            data["geomagnetic_status"] = (
                                "G4/G5 Severe Geomagnetic Storm"
                            )
            except Exception as e:
                logger.warning("NOAA Kp-index fetch failed: %s", e)

            try:
                res2 = await client.get(NOAA_SWPC_SOLAR_FLARES)
                if res2.status_code == 200:
                    flares = res2.json()
                    if isinstance(flares, list) and flares:
                        data["solar_activity"] = "Active Solar Monitoring"
            except Exception as e:
                logger.debug("NOAA Solar Flares fetch failed: %s", e)

        return data
