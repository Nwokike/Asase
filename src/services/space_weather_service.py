"""NOAA Space Weather Prediction Center client with Pydantic v2."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from core.constants import (
    NOAA_SWPC_KP_FORECAST,
    NOAA_SWPC_KP_INDEX,
    NOAA_SWPC_SOLAR_FLARES,
)
from core.network import NetworkManager
from models.space_weather import SpaceWeatherTelemetry

logger = logging.getLogger("asase.space_weather")

# The GOES channel used for official flare classification
_XRAY_CHANNEL = "0.1-0.8nm"


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


def _parse_xray_series(flares: list) -> list[float]:
    """Extract the 0.1-0.8nm flux trace, downscaled to nW/m² (~72 pts)."""
    try:
        vals = [
            float(f["flux"]) * 1e9
            for f in flares
            if isinstance(f, dict)
            and f.get("energy") == _XRAY_CHANNEL
            and f.get("flux") is not None
        ]
    except (TypeError, ValueError, KeyError):
        return []
    if not vals:
        return []
    step = max(1, len(vals) // 72)
    return vals[::step][-72:]


def _parse_kp_forecast(rows: list) -> list[dict]:
    """Keep the next ~24h of predicted Kp entries (3h cadence → 8 slots)."""
    now = datetime.now(UTC)
    out: list[dict] = []
    for r in rows:
        if not isinstance(r, dict) or r.get("observed") != "predicted":
            continue
        try:
            when = datetime.fromisoformat(str(r.get("time_tag", "")))
        except ValueError:
            continue
        if when.tzinfo is None:
            when = when.replace(tzinfo=UTC)  # SWPC stamps are UTC, unstamped
        if when <= now:
            continue
        try:
            kp = float(r.get("kp", 0.0))
        except (TypeError, ValueError):
            continue
        out.append({"time_tag": str(r.get("time_tag", "")), "kp": kp})
        if len(out) >= 8:
            break
    return out


class SpaceWeatherService:
    @staticmethod
    async def fetch_space_weather() -> dict:
        kp_val = 0.0
        status = "Quiet (Normal)"
        solar = "Normal"
        flare_class = ""
        raw_kp: list = []
        xray_flux: list[float] = []
        kp_forecast: list[dict] = []

        client = NetworkManager.get_client()

        async def _fetch_noaa(url: str):
            try:
                res = await client.get(url)
                return res.json() if res.status_code == 200 else None
            except Exception as ex:
                logger.debug("NOAA fetch failed for %s: %s", url, ex)
                return None

        # Fetch all 3 NOAA space weather feeds concurrently
        import asyncio

        kp_data, flares, forecast_rows = await asyncio.gather(
            _fetch_noaa(NOAA_SWPC_KP_INDEX),
            _fetch_noaa(NOAA_SWPC_SOLAR_FLARES),
            _fetch_noaa(NOAA_SWPC_KP_FORECAST),
        )

        if isinstance(kp_data, list) and len(kp_data) >= 1:
            latest = kp_data[-1]
            if isinstance(latest, dict):
                kp_val = float(
                    latest.get(
                        "Kp",
                        latest.get(
                            "kp",
                            latest.get("estimated_kp", latest.get("kp_index", 0.0)),
                        ),
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

        if isinstance(flares, list) and flares:
            solar, flare_class = _parse_flare_class(flares)
            xray_flux = _parse_xray_series(flares)

        if isinstance(forecast_rows, list):
            kp_forecast = _parse_kp_forecast(forecast_rows)

        telemetry = SpaceWeatherTelemetry(
            kp_index=kp_val,
            geomagnetic_status=status,
            solar_activity=solar,
            raw_kp=raw_kp if isinstance(raw_kp, list) else [],
            flare_class=flare_class,
            xray_flux=xray_flux if isinstance(xray_flux, list) else [],
            kp_forecast=kp_forecast if isinstance(kp_forecast, list) else [],
        )
        return telemetry.model_dump()
