"""Open-Meteo Weather, Air Quality, GloFAS Flood, and Marine client — concurrent."""

from __future__ import annotations

import asyncio
import logging

from core.constants import (
    OPEN_METEO_AIR_QUALITY,
    OPEN_METEO_FLOOD,
    OPEN_METEO_FORECAST,
    OPEN_METEO_MARINE,
)
from core.validators import conditional_get_json
from models.atmospheric import (
    CurrentAirQuality,
    CurrentMarine,
    CurrentWeather,
    GloFASDaily,
)

logger = logging.getLogger("asase.atmospheric")


async def _fetch_json(url: str) -> dict:
    status, payload = await conditional_get_json(url, log_name="Open-Meteo")
    if status in (200, 304) and isinstance(payload, dict):
        return payload
    return {}


def _validate_section(model, data: dict, name: str) -> dict:
    """Validate a feed section through its pydantic model.

    Returns the validated dump on success; on shape drift the RAW data
    passes through untouched (today's behavior) with a debug log — a
    model/upstream mismatch must never blank a working feed.
    """
    if not isinstance(data, dict) or not data:
        return data
    try:
        validated = model.model_validate(data)
        return validated.model_dump()
    except Exception as ex:
        logger.debug("%s shape drift, passing raw: %s", name, ex)
        return data


class AtmosphericService:
    @staticmethod
    async def fetch_location_telemetry(lat: float, lon: float) -> dict:
        """Fetch weather, AQI, flood, marine concurrently."""
        weather_url = (
            f"{OPEN_METEO_FORECAST}?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,surface_pressure,wind_speed_10m,wind_gusts_10m,uv_index,cape"
            "&hourly=temperature_2m,precipitation_probability,wind_gusts_10m,cape,cloud_cover,cloud_cover_low,cloud_cover_high,dew_point_2m"
            "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,wind_gusts_10m_max"
            "&timezone=auto&past_days=3&forecast_days=7"
        )
        aqi_url = (
            f"{OPEN_METEO_AIR_QUALITY}?latitude={lat}&longitude={lon}"
            "&current=european_aqi,us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,dust,ammonia"
            "&hourly=european_aqi,us_aqi,pm2_5,pm10,alder_pollen,birch_pollen,grass_pollen,ragweed_pollen"
            "&past_days=3&forecast_days=3"
        )
        flood_url = (
            f"{OPEN_METEO_FLOOD}?latitude={lat}&longitude={lon}"
            "&daily=river_discharge,river_discharge_mean,river_discharge_median,river_discharge_max,river_discharge_min"
            "&forecast_days=7"
        )
        marine_url = (
            f"{OPEN_METEO_MARINE}?latitude={lat}&longitude={lon}"
            "&current=wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height,swell_wave_period,swell_wave_direction"
        )

        weather, air_quality, flood, marine = await asyncio.gather(
            _fetch_json(weather_url),
            _fetch_json(aqi_url),
            _fetch_json(flood_url),
            _fetch_json(marine_url),
            return_exceptions=False,
        )

        if not marine:
            logger.debug("Marine fetch (likely inland) for (%s, %s)", lat, lon)

        # Typed validation with raw passthrough on drift — the models are
        # the contract, but a contract mismatch must not blank live feeds.
        # Empty sections stay empty (no shape change on total failure).
        if isinstance(weather, dict) and weather.get("current"):
            weather = {
                **weather,
                "current": _validate_section(
                    CurrentWeather, weather["current"], "weather.current"
                ),
            }
        if isinstance(air_quality, dict) and air_quality.get("current"):
            air_quality = {
                **air_quality,
                "current": _validate_section(
                    CurrentAirQuality,
                    air_quality["current"],
                    "air_quality.current",
                ),
            }
        if isinstance(flood, dict) and flood.get("daily"):
            flood = {
                **flood,
                "daily": _validate_section(GloFASDaily, flood["daily"], "flood.daily"),
            }
        if isinstance(marine, dict) and marine.get("current"):
            marine = {
                **marine,
                "current": _validate_section(
                    CurrentMarine, marine["current"], "marine.current"
                ),
            }

        return {
            "weather": weather,
            "air_quality": air_quality,
            "flood": flood,
            "marine": marine,
        }
