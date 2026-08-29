"""NASA EONET and GDACS disaster schemas using Pydantic v2."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class EonetCategory(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: str
    title: str


class EonetGeometry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    date: str = ""
    type: str = "Point"
    coordinates: list = Field(default_factory=list)

    @property
    def point_coords(self) -> tuple[float, float]:
        """Extracts (longitude, latitude) safely from Point or Polygon."""
        coords = self.coordinates
        if not coords:
            return (0.0, 0.0)
        if isinstance(coords[0], (int, float)) and len(coords) >= 2:
            return (float(coords[0]), float(coords[1]))
        if isinstance(coords[0], list) and coords[0]:
            first = coords[0]
            if isinstance(first[0], (int, float)) and len(first) >= 2:
                return (float(first[0]), float(first[1]))
            if isinstance(first[0], list) and first[0]:
                return (float(first[0][0]), float(first[0][1]))
        return (0.0, 0.0)


class EonetEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    id: str
    title: str
    description: str | None = None
    link: str = ""
    categories: list[EonetCategory] = Field(default_factory=list)
    geometry: list[EonetGeometry] = Field(default_factory=list)

    @computed_field
    @property
    def hazard_type(
        self,
    ) -> Literal["wildfire", "storm", "volcano", "flood", "disaster"]:
        cat_str = " ".join(
            c.id.lower() + " " + c.title.lower() for c in self.categories
        )
        if "wildfire" in cat_str or "fire" in cat_str:
            return "wildfire"
        if "storm" in cat_str or "cyclone" in cat_str or "hurricane" in cat_str:
            return "storm"
        if "volcano" in cat_str:
            return "volcano"
        if "flood" in cat_str:
            return "flood"
        return "disaster"

    @computed_field
    @property
    def primary_coordinates(self) -> tuple[float, float]:
        if not self.geometry:
            return (0.0, 0.0)
        return self.geometry[-1].point_coords

    def to_map_dict(self) -> dict:
        lon, lat = self.primary_coordinates
        cat_id = self.categories[0].id if self.categories else "hazard"
        cat_title = self.categories[0].title if self.categories else "Natural Event"
        latest_date = self.geometry[-1].date if self.geometry else ""
        return {
            "id": self.id,
            "title": self.title,
            "category_id": cat_id,
            "category_title": cat_title,
            "date": latest_date,
            "longitude": lon,
            "latitude": lat,
            "url": self.link,
            "type": self.hazard_type,
        }


class EonetResponse(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    title: str = ""
    events: list[EonetEvent] = Field(default_factory=list)
