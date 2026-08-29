"""Open-Meteo weather, air quality, flood, and marine schemas using Pydantic v2."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class CurrentWeather(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    time: str = ""
    temperature_2m: float = 0.0
    relative_humidity_2m: float = 0.0
    apparent_temperature: float = 0.0
    precipitation: float = 0.0
    rain: float = 0.0
    weather_code: int = 0
    surface_pressure: float = 1013.25
    wind_speed_10m: float = 0.0
    wind_gusts_10m: float = 0.0
    uv_index: float = 0.0
    cape: float | None = 0.0

    @computed_field
    @property
    def storm_risk_category(self) -> Literal["low", "moderate", "high", "extreme"]:
        cape_val = self.cape or 0.0
        if cape_val >= 2500:
            return "extreme"
        if cape_val >= 1000:
            return "high"
        if cape_val >= 300:
            return "moderate"
        return "low"


class CurrentAirQuality(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    time: str = ""
    european_aqi: int | None = 0
    us_aqi: int | None = 0
    pm10: float | None = 0.0
    pm2_5: float | None = 0.0
    carbon_monoxide: float | None = 0.0
    nitrogen_dioxide: float | None = 0.0
    sulphur_dioxide: float | None = 0.0
    ozone: float | None = 0.0
    dust: float | None = 0.0

    @computed_field
    @property
    def aqi_health_descriptor(self) -> str:
        aqi = self.us_aqi or 0
        if aqi <= 50:
            return "Good (Optimal)"
        if aqi <= 100:
            return "Moderate (Acceptable)"
        if aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        if aqi <= 200:
            return "Unhealthy (High Pollution)"
        if aqi <= 300:
            return "Very Unhealthy (Alert)"
        return "Hazardous (Emergency)"


class GloFASDaily(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    time: list[str] = Field(default_factory=list)
    river_discharge: list[float | None] = Field(default_factory=list)
    river_discharge_mean: list[float | None] = Field(default_factory=list)
    river_discharge_median: list[float | None] = Field(default_factory=list)
    river_discharge_max: list[float | None] = Field(default_factory=list)
    river_discharge_min: list[float | None] = Field(default_factory=list)


class CurrentMarine(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    wave_height: float | None = None
    wave_direction: float | None = None
    wave_period: float | None = None
    wind_wave_height: float | None = None
    swell_wave_height: float | None = None


class TelemetryDossier(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    weather: dict = Field(default_factory=dict)
    air_quality: dict = Field(default_factory=dict)
    flood: dict = Field(default_factory=dict)
    marine: dict = Field(default_factory=dict)
