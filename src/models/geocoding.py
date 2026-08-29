"""Open-Meteo geocoding schemas using Pydantic v2."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


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


class GeocodingResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    results: list[GeocodingLocation] = Field(default_factory=list)
