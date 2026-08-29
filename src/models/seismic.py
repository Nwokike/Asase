"""USGS Earthquake GeoJSON schemas using Pydantic v2."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class GeoJsonPointGeometry(BaseModel):
    model_config = ConfigDict(frozen=True)
    type: Literal["Point"] = "Point"
    coordinates: list[float]  # [longitude, latitude, depth_km]

    @property
    def longitude(self) -> float:
        return self.coordinates[0] if len(self.coordinates) > 0 else 0.0

    @property
    def latitude(self) -> float:
        return self.coordinates[1] if len(self.coordinates) > 1 else 0.0

    @property
    def depth_km(self) -> float:
        return self.coordinates[2] if len(self.coordinates) > 2 else 0.0


class EarthquakeProperties(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    mag: float = Field(default=0.0, description="Earthquake magnitude")
    place: str = Field(default="Unknown location")
    time: int = Field(description="Epoch time in milliseconds")
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

    @computed_field
    @property
    def utc_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.time / 1000.0, tz=UTC)

    @computed_field
    @property
    def formatted_time(self) -> str:
        return self.utc_datetime.strftime("%Y-%m-%d %H:%M UTC")

    @computed_field
    @property
    def has_tsunami_warning(self) -> bool:
        return self.tsunami == 1

    @computed_field
    @property
    def severity_level(self) -> Literal["low", "moderate", "high", "critical"]:
        if self.mag >= 6.5 or self.alert in ("red", "orange"):
            return "critical"
        if self.mag >= 4.5 or self.alert == "yellow":
            return "high"
        if self.mag >= 3.0:
            return "moderate"
        return "low"


class EarthquakeFeature(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    id: str
    type: Literal["Feature"] = "Feature"
    properties: EarthquakeProperties
    geometry: GeoJsonPointGeometry

    def to_map_dict(self) -> dict:
        """Normalized dictionary for UI consumption and flet-map markers."""
        return {
            "id": self.id,
            "title": self.properties.title,
            "place": self.properties.place,
            "magnitude": self.properties.mag,
            "depth_km": self.geometry.depth_km,
            "longitude": self.geometry.longitude,
            "latitude": self.geometry.latitude,
            "tsunami": self.properties.has_tsunami_warning,
            "alert": self.properties.alert or "green",
            "mmi": self.properties.mmi or 0.0,
            "time_str": self.properties.formatted_time,
            "url": self.properties.url,
            "type": "earthquake",
            "severity": self.properties.severity_level,
        }


class EarthquakeFeatureCollection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[EarthquakeFeature] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
