"""NOAA Space Weather Prediction Center client with Pydantic v2."""

from __future__ import annotations

import logging

from core.constants import NOAA_SWPC_KP_INDEX, NOAA_SWPC_SOLAR_FLARES
from core.network import NetworkManager
from models.space_weather import SpaceWeatherTelemetry

logger = logging.getLogger("asase.space_weather")


def _parse_flare_class(flares: list) -> tuple[str, str]:
    """Extract strongest flare class from GOES xray array."""
    best = ""
    best_rank = -1
    rank = {"A": 0, "B": 1, "C": 2, "M": 3, "X": 4}
    for f in flares:
        if isinstance(f, dict):
            cls = (
                str(f.get("classType") or f.get("class_type") or f.get("class") or "")
                .strip()
                .upper()
            )
            if cls and cls[0] in rank and rank[cls[0]] > best_rank:
                best = cls
                best_rank = rank[cls[0]]
            # fallback: flux field
            if not best:
                flux = f.get("flux") or f.get("current_flux")
                try:
                    v = float(str(flux))
                    if v >= 1e-4:
                        best = "X"
                    elif v >= 1e-5:
                        best = "M"
                    elif v >= 1e-6:
                        best = "C"
                except Exception:
                    pass
    if best:
        return f"Active — {best}-class flare detected", best
    return "Active Solar Monitoring", ""


class SpaceWeatherService:
    @staticmethod
    async def fetch_space_weather() -> dict:
        kp_val = 0.0
        status = "Quiet (Normal)"
        solar = "Normal"
        flare_class = ""
        raw_kp: list = []

        client = NetworkManager.get_client()

        try:
            res = await client.get(NOAA_SWPC_KP_INDEX)
            if res.status_code == 200:
                kp_data = res.json()
                if isinstance(kp_data, list) and len(kp_data) >= 1:
                    latest = kp_data[-1]
                    if isinstance(latest, dict):
                        kp_val = float(
                            latest.get(
                                "Kp",
                                latest.get("estimated_kp", latest.get("kp_index", 0.0)),
                            )
                        )
                    elif isinstance(latest, list) and len(latest) > 1:
                        kp_val = float(latest[1])
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
                    logger.info("NOAA SWPC: Kp %.2f (%s)", kp_val, status)
        except Exception as e:
            logger.warning("NOAA Kp-index fetch failed: %s", e)

        try:
            res2 = await client.get(NOAA_SWPC_SOLAR_FLARES)
            if res2.status_code == 200:
                flares = res2.json()
                if isinstance(flares, list) and flares:
                    solar, flare_class = _parse_flare_class(flares)
        except Exception as e:
            logger.debug("NOAA Solar Flares fetch failed: %s", e)

        telemetry = SpaceWeatherTelemetry(
            kp_index=kp_val,
            geomagnetic_status=status,
            solar_activity=solar,
            raw_kp=raw_kp if isinstance(raw_kp, list) else [],
        )
        d = telemetry.model_dump()
        d["flare_class"] = flare_class
        return d
