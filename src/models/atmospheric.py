"""Open-Meteo weather, air quality, flood, and marine schemas — stdlib dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from models._coerce import (
    opt_float,
    opt_float_list,
    opt_int,
    opt_list,
    opt_str,
)
from models._model import DataModel


@dataclass(frozen=True, kw_only=True)
class CurrentWeather(DataModel):
    _COMPUTED = ("storm_risk_category",)

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

    @classmethod
    def model_validate(cls, data) -> CurrentWeather:
        if not isinstance(data, dict):
            raise TypeError("CurrentWeather: expected object")
        return cls(
            time=opt_str(data, "time", ""),
            temperature_2m=opt_float(data, "temperature_2m", 0.0),
            relative_humidity_2m=opt_float(data, "relative_humidity_2m", 0.0),
            apparent_temperature=opt_float(data, "apparent_temperature", 0.0),
            precipitation=opt_float(data, "precipitation", 0.0),
            rain=opt_float(data, "rain", 0.0),
            weather_code=opt_int(data, "weather_code", 0),
            surface_pressure=opt_float(data, "surface_pressure", 1013.25),
            wind_speed_10m=opt_float(data, "wind_speed_10m", 0.0),
            wind_gusts_10m=opt_float(data, "wind_gusts_10m", 0.0),
            uv_index=opt_float(data, "uv_index", 0.0),
            cape=opt_float(data, "cape", 0.0),
        )

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


@dataclass(frozen=True, kw_only=True)
class CurrentAirQuality(DataModel):
    _COMPUTED = ("aqi_health_descriptor",)

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

    @classmethod
    def model_validate(cls, data) -> CurrentAirQuality:
        if not isinstance(data, dict):
            raise TypeError("CurrentAirQuality: expected object")
        return cls(
            time=opt_str(data, "time", ""),
            european_aqi=opt_int(data, "european_aqi", 0),
            us_aqi=opt_int(data, "us_aqi", 0),
            pm10=opt_float(data, "pm10", 0.0),
            pm2_5=opt_float(data, "pm2_5", 0.0),
            carbon_monoxide=opt_float(data, "carbon_monoxide", 0.0),
            nitrogen_dioxide=opt_float(data, "nitrogen_dioxide", 0.0),
            sulphur_dioxide=opt_float(data, "sulphur_dioxide", 0.0),
            ozone=opt_float(data, "ozone", 0.0),
            dust=opt_float(data, "dust", 0.0),
        )

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


@dataclass(frozen=True, kw_only=True)
class GloFASDaily(DataModel):
    time: list = field(default_factory=list)
    river_discharge: list = field(default_factory=list)
    river_discharge_mean: list = field(default_factory=list)
    river_discharge_median: list = field(default_factory=list)
    river_discharge_max: list = field(default_factory=list)
    river_discharge_min: list = field(default_factory=list)

    @classmethod
    def model_validate(cls, data) -> GloFASDaily:
        if not isinstance(data, dict):
            raise TypeError("GloFASDaily: expected object")
        return cls(
            time=opt_list(data, "time"),
            river_discharge=opt_float_list(data, "river_discharge"),
            river_discharge_mean=opt_float_list(data, "river_discharge_mean"),
            river_discharge_median=opt_float_list(data, "river_discharge_median"),
            river_discharge_max=opt_float_list(data, "river_discharge_max"),
            river_discharge_min=opt_float_list(data, "river_discharge_min"),
        )


@dataclass(frozen=True, kw_only=True)
class CurrentMarine(DataModel):
    wave_height: float | None = None
    wave_direction: float | None = None
    wave_period: float | None = None
    wind_wave_height: float | None = None
    swell_wave_height: float | None = None

    @classmethod
    def model_validate(cls, data) -> CurrentMarine:
        if not isinstance(data, dict):
            raise TypeError("CurrentMarine: expected object")
        return cls(
            wave_height=opt_float(data, "wave_height", None),
            wave_direction=opt_float(data, "wave_direction", None),
            wave_period=opt_float(data, "wave_period", None),
            wind_wave_height=opt_float(data, "wind_wave_height", None),
            swell_wave_height=opt_float(data, "swell_wave_height", None),
        )


@dataclass(frozen=True, kw_only=True)
class TelemetryDossier(DataModel):
    weather: dict = field(default_factory=dict)
    air_quality: dict = field(default_factory=dict)
    flood: dict = field(default_factory=dict)
    marine: dict = field(default_factory=dict)
