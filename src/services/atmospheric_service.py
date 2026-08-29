"""Open-Meteo Weather, Air Quality, and GloFAS River Flood client (100% Free & No-Auth)."""

from __future__ import annotations

import logging

import httpx

from core.constants import (
    OPEN_METEO_AIR_QUALITY,
    OPEN_METEO_FLOOD,
    OPEN_METEO_FORECAST,
    OPEN_METEO_MARINE,
)

logger = logging.getLogger("asase.atmospheric")


class AtmosphericService:
    @staticmethod
    async def fetch_location_telemetry(lat: float, lon: float) -> dict:
        """Fetch comprehensive atmospheric, AQI, flood risk, and weather telemetry with past_days=3."""
        telemetry = {
            "weather": {},
            "air_quality": {},
            "flood": {},
            "marine": {},
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
            # 1. Weather & Storm Forecast + 3 Days Past History
            weather_url = (
                f"{OPEN_METEO_FORECAST}?latitude={lat}&longitude={lon}"
                "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,surface_pressure,wind_speed_10m,wind_gusts_10m,uv_index,cape"
                "&hourly=temperature_2m,precipitation_probability,wind_gusts_10m,cape&past_days=3&forecast_days=3"
            )
            try:
                res = await client.get(weather_url)
                if res.status_code == 200:
                    telemetry["weather"] = res.json()
            except Exception as e:
                logger.warning("Weather fetch error for (%s, %s): %s", lat, lon, e)

            # 2. Air Quality Index & Pollutants + 3 Days Past History
            aqi_url = (
                f"{OPEN_METEO_AIR_QUALITY}?latitude={lat}&longitude={lon}"
                "&current=european_aqi,us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,dust"
                "&hourly=european_aqi,us_aqi,pm2_5,pm10&past_days=3&forecast_days=3"
            )
            try:
                res = await client.get(aqi_url)
                if res.status_code == 200:
                    telemetry["air_quality"] = res.json()
            except Exception as e:
                logger.warning("AQI fetch error for (%s, %s): %s", lat, lon, e)

            # 3. GloFAS River Flood Forecasting (7-day river discharge)
            flood_url = (
                f"{OPEN_METEO_FLOOD}?latitude={lat}&longitude={lon}"
                "&daily=river_discharge,river_discharge_mean,river_discharge_median,river_discharge_max,river_discharge_min"
                "&forecast_days=7"
            )
            try:
                res = await client.get(flood_url)
                if res.status_code == 200:
                    telemetry["flood"] = res.json()
            except Exception as e:
                logger.warning("Flood forecast error for (%s, %s): %s", lat, lon, e)

            # 4. Marine / Coastal Conditions
            marine_url = (
                f"{OPEN_METEO_MARINE}?latitude={lat}&longitude={lon}"
                "&current=wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height"
            )
            try:
                res = await client.get(marine_url)
                if res.status_code == 200:
                    telemetry["marine"] = res.json()
            except Exception as e:
                logger.debug(
                    "Marine fetch (likely inland) for (%s, %s): %s", lat, lon, e
                )

        return telemetry
