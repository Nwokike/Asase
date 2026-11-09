"""Open-Meteo geocoding schemas — stdlib dataclasses, no pydantic."""

from __future__ import annotations

from dataclasses import dataclass, field

from models._coerce import as_float, as_str, opt_float, opt_int, opt_str
from models._model import DataModel, parse_models


@dataclass(frozen=True, kw_only=True)
class GeocodingLocation(DataModel):
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

    @classmethod
    def model_validate(cls, data) -> GeocodingLocation:
        if not isinstance(data, dict):
            raise TypeError("GeocodingLocation: expected object")
        # Upstream nulls on display strings must not reject the whole
        # response — fall back to the field default instead (the old
        # before-validators did exactly this). name/latitude/longitude
        # stay required: a result without them is Null Island bait.
        return cls(
            id=opt_int(data, "id", None),
            name=as_str(data, "name"),
            latitude=as_float(data, "latitude"),
            longitude=as_float(data, "longitude"),
            elevation=opt_float(data, "elevation", 0.0),
            country=opt_str(data, "country", ""),
            country_code=opt_str(data, "country_code", ""),
            admin1=opt_str(data, "admin1", ""),
            timezone=opt_str(data, "timezone", "UTC"),
            population=opt_int(data, "population", 0),
        )


@dataclass(frozen=True, kw_only=True)
class GeocodingResponse(DataModel):
    results: list[GeocodingLocation] = field(default_factory=list)

    @classmethod
    def model_validate(cls, data) -> GeocodingResponse:
        if not isinstance(data, dict):
            raise TypeError("GeocodingResponse: expected object")
        return cls(
            results=parse_models(data, "results", GeocodingLocation.model_validate)
        )
