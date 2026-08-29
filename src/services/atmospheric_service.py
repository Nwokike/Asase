"""Open-Meteo Weather, Air Quality, GloFAS Flood, and Marine client."""

from __future__ import annotations

import logging

from core.constants import (
    OPEN_METEO_AIR_QUALITY,
    OPEN_METEO_FLOOD,
    OPEN_METEO_FORECAST,
    OPEN_METEO_MARINE,
)
from core.network import NetworkManager

logger = logging.getLogger("asase.atmospheric")


class AtmosphericService:
    @staticmethod
    async def fetch_location_telemetry(lat: float, lon: float) -> dict:
        """Fetch comprehensive atmospheric, pollen, AQI, GloFAS river flood, and marine telemetry."""
        telemetry = {
            "weather": {},
            "air_quality": {},
            "flood": {},
            "marine": {},
        }
        client = NetworkManager.get_client()

        # 1. Weather & Storm Dynamics
        weather_url = (
            f"{OPEN_METEO_FORECAST}?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,surface_pressure,wind_speed_10m,wind_gusts_10m,uv_index,cape"
            "&hourly=temperature_2m,precipitation_probability,wind_gusts_10m,cape,cloud_cover,cloud_cover_low,cloud_cover_high,dew_point_2m"
            "&past_days=3&forecast_days=3"
        )
        try:
            res = await client.get(weather_url)
            if res.status_code == 200:
                telemetry["weather"] = res.json()
        except Exception as e:
            logger.warning("Weather fetch error for (%s, %s): %s", lat, lon, e)

        # 2. Air Quality Index & Biogenic Pollen Spectrum
        aqi_url = (
            f"{OPEN_METEO_AIR_QUALITY}?latitude={lat}&longitude={lon}"
            "&current=european_aqi,us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,dust,ammonia"
            "&hourly=european_aqi,us_aqi,pm2_5,pm10,alder_pollen,birch_pollen,grass_pollen,ragweed_pollen"
            "&past_days=3&forecast_days=3"
        )
        try:
            res = await client.get(aqi_url)
            if res.status_code == 200:
                telemetry["air_quality"] = res.json()
        except Exception as e:
            logger.warning("AQI fetch error for (%s, %s): %s", lat, lon, e)

        # 3. GloFAS River Flood Forecasting
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

        # 4. Marine & Coastal Wave Swell
        marine_url = (
            f"{OPEN_METEO_MARINE}?latitude={lat}&longitude={lon}"
            "&current=wave_height,wave_direction,wave_period,wind_wave_height,swell_wave_height,swell_wave_period,swell_wave_direction"
        )
        try:
            res = await client.get(marine_url)
            if res.status_code == 200:
                telemetry["marine"] = res.json()
        except Exception as e:
            logger.debug("Marine fetch (likely inland) for (%s, %s): %s", lat, lon, e)

        return telemetry
