"""USGS Earthquake GeoJSON schemas — stdlib dataclasses, no pydantic.

Validation semantics live in models/_coerce.py: nulls fall back to
defaults, wrong-typed values raise so the service's per-record
try/except skips exactly the records pydantic's ValidationError skipped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from models._coerce import (
    as_int,
    as_str,
    opt_dict,
    opt_float,
    opt_int,
    opt_list,
    opt_str,
)
from models._model import DataModel, parse_models


@dataclass(frozen=True, kw_only=True)
class GeoJsonPointGeometry(DataModel):
    type: str = "Point"
    coordinates: list = field(default_factory=list)  # [lon, lat, depth_km]

    @classmethod
    def model_validate(cls, data) -> GeoJsonPointGeometry:
        if not isinstance(data, dict):
            raise TypeError("GeoJsonPointGeometry: expected object")
        return cls(coordinates=opt_list(data, "coordinates"))

    @property
    def longitude(self) -> float:
        return self.coordinates[0] if len(self.coordinates) > 0 else 0.0

    @property
    def latitude(self) -> float:
        return self.coordinates[1] if len(self.coordinates) > 1 else 0.0

    @property
    def depth_km(self) -> float:
        return self.coordinates[2] if len(self.coordinates) > 2 else 0.0


@dataclass(frozen=True, kw_only=True)
class EarthquakeProperties(DataModel):
    _COMPUTED = (
        "utc_datetime",
        "formatted_time",
        "has_tsunami_warning",
        "severity_level",
    )

    mag: float = 0.0
    place: str = "Unknown location"
    time: int  # epoch milliseconds — required, a record without it is skipped
    updated: int | None = None
    url: str = ""
    detail: str = ""
    felt: int | None = None
    cdi: float | None = None
    mmi: float | None = None
    alert: str | None = "green"  # green, yellow, orange, red
    status: str = "reviewed"
    tsunami: int = 0
    sig: int = 0
    net: str = ""
    code: str = ""
    magType: str = "ml"
    title: str = "Earthquake"

    @classmethod
    def model_validate(cls, data) -> EarthquakeProperties:
        if not isinstance(data, dict):
            raise TypeError("EarthquakeProperties: expected object")
        # USGS occasionally emits explicit null magnitudes; a null on one
        # feature must not reject the whole batch. Coerce to the default.
        mag = data.get("mag")
        if mag is None:
            mag = 0.0
        elif isinstance(mag, bool) or not isinstance(mag, (int, float)):
            raise ValueError("mag: expected number")
        alert = data.get("alert", "green")
        if alert is not None and not isinstance(alert, str):
            raise ValueError("alert: expected string")
        return cls(
            mag=float(mag),
            place=opt_str(data, "place", "Unknown location"),
            time=as_int(data, "time"),
            updated=opt_int(data, "updated", None),
            url=opt_str(data, "url", ""),
            detail=opt_str(data, "detail", ""),
            felt=opt_int(data, "felt", None),
            cdi=opt_float(data, "cdi", None),
            mmi=opt_float(data, "mmi", None),
            alert=alert,
            status=opt_str(data, "status", "reviewed"),
            tsunami=opt_int(data, "tsunami", 0),
            sig=opt_int(data, "sig", 0),
            net=opt_str(data, "net", ""),
            code=opt_str(data, "code", ""),
            magType=opt_str(data, "magType", "ml"),
            title=opt_str(data, "title", "Earthquake"),
        )

    @property
    def utc_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.time / 1000.0, tz=UTC)

    @property
    def formatted_time(self) -> str:
        return self.utc_datetime.strftime("%Y-%m-%d %H:%M UTC")

    @property
    def has_tsunami_warning(self) -> bool:
        return self.tsunami == 1

    @property
    def severity_level(self) -> Literal["low", "moderate", "high", "critical"]:
        if self.mag >= 6.5 or self.alert in ("red", "orange"):
            return "critical"
        if self.mag >= 4.5 or self.alert == "yellow":
            return "high"
        if self.mag >= 3.0:
            return "moderate"
        return "low"


@dataclass(frozen=True, kw_only=True)
class EarthquakeFeature(DataModel):
    id: str
    type: str = "Feature"
    properties: EarthquakeProperties
    # USGS emits explicit null geometry for deleted/superseded events.
    geometry: GeoJsonPointGeometry | None = None

    @classmethod
    def model_validate(cls, data) -> EarthquakeFeature:
        if not isinstance(data, dict):
            raise TypeError("EarthquakeFeature: expected object")
        raw_geometry = data.get("geometry")
        return cls(
            id=as_str(data, "id"),
            properties=EarthquakeProperties.model_validate(data.get("properties")),
            geometry=None
            if raw_geometry is None
            else GeoJsonPointGeometry.model_validate(raw_geometry),
        )

    def to_map_dict(self) -> dict:
        """Normalized dictionary for UI consumption and flet-map markers."""
        geometry = self.geometry or GeoJsonPointGeometry()
        return {
            "id": self.id,
            "title": self.properties.title,
            "place": self.properties.place,
            "magnitude": self.properties.mag,
            "depth_km": geometry.depth_km,
            "longitude": geometry.longitude,
            "latitude": geometry.latitude,
            "tsunami": self.properties.has_tsunami_warning,
            "alert": self.properties.alert or "green",
            "mmi": self.properties.mmi or 0.0,
            "time_str": self.properties.formatted_time,
            "url": self.properties.url,
            "type": "earthquake",
            "severity": self.properties.severity_level,
        }


@dataclass(frozen=True, kw_only=True)
class EarthquakeFeatureCollection(DataModel):
    type: str = "FeatureCollection"
    features: list[EarthquakeFeature] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @classmethod
    def model_validate(cls, data) -> EarthquakeFeatureCollection:
        if not isinstance(data, dict):
            raise TypeError("EarthquakeFeatureCollection: expected object")
        return cls(
            # Strict: one bad feature raises, so the service's whole-batch
            # fast path falls back to per-feature parsing (fail open).
            features=parse_models(data, "features", EarthquakeFeature.model_validate),
            metadata=opt_dict(data, "metadata"),
        )
