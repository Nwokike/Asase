"""NOAA Space Weather Prediction Center client with Pydantic v2."""

from __future__ import annotations

import logging

from core.constants import NOAA_SWPC_KP_INDEX, NOAA_SWPC_SOLAR_FLARES
from core.network import NetworkManager
from models.space_weather import SpaceWeatherTelemetry

logger = logging.getLogger("asase.space_weather")


class SpaceWeatherService:
    @staticmethod
    async def fetch_space_weather() -> dict:
        """Fetch real-time geomagnetic storm Kp-index and solar flare flux."""
        kp_val = 0.0
        status = "Quiet (Normal)"
        solar = "Normal"
        raw_kp: list = []

        client = NetworkManager.get_client()

        # 1. Planetary Kp-index
        try:
            res = await client.get(NOAA_SWPC_KP_INDEX)
            if res.status_code == 200:
                kp_data = res.json()
                if isinstance(kp_data, list) and len(kp_data) >= 1:
                    latest = kp_data[-1]
                    if isinstance(latest, dict):
                        kp_val = float(
                            latest.get("estimated_kp", latest.get("kp_index", 0.0))
                        )
                    elif isinstance(latest, list) and len(latest) > 1:
                        kp_val = float(latest[1])
                    else:
                        kp_val = 0.0

                    raw_kp = kp_data[-12:]

                    if kp_val < 3.0:
                        status = "Quiet (Normal)"
                    elif kp_val < 5.0:
                        status = "Unsettled / Active"
                    elif kp_val < 6.0:
                        status = "G1 Minor Geomagnetic Storm"
                    elif kp_val < 7.0:
                        status = "G2 Moderate Geomagnetic Storm"
                    elif kp_val < 8.0:
                        status = "G3 Strong Geomagnetic Storm"
                    else:
                        status = "G4/G5 Severe Geomagnetic Storm"
                    logger.info("NOAA SWPC: Validated Kp %.2f (%s)", kp_val, status)
        except Exception as e:
            logger.warning("NOAA Kp-index fetch failed: %s", e)

        # 2. GOES Solar X-Ray Flares
        try:
            res2 = await client.get(NOAA_SWPC_SOLAR_FLARES)
            if res2.status_code == 200:
                flares = res2.json()
                if isinstance(flares, list) and flares:
                    solar = "Active Solar Monitoring"
        except Exception as e:
            logger.debug("NOAA Solar Flares fetch failed: %s", e)

        telemetry = SpaceWeatherTelemetry(
            kp_index=kp_val,
            geomagnetic_status=status,
            solar_activity=solar,
            raw_kp=raw_kp if isinstance(raw_kp, list) else [],
        )

        return telemetry.model_dump()
