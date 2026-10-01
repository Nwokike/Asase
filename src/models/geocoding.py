"""Open-Meteo geocoding schemas using Pydantic v2."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GeocodingLocation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: int | None = None
    name: str
    latitude: float
    longitude: float
    elevation: float | None = 0.0
    country: str = ""
    country_code: str = ""
    admin1: str = ""
    timezone: str = "UTC"
    population: int = 0

    @field_validator("country", "country_code", "admin1", "timezone", mode="before")
    @classmethod
    def _null_str_to_default(cls, v, info):
        # Upstream nulls on display strings must not reject the whole
        # response — fall back to the field default instead.
        if v is None:
            return cls.model_fields[info.field_name].default
        return v

    @field_validator("population", mode="before")
    @classmethod
    def _null_population_to_zero(cls, v):
        return 0 if v is None else v


class GeocodingResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    results: list[GeocodingLocation] = Field(default_factory=list)
