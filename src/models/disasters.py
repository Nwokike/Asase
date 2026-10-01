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
        """Extracts (longitude, latitude) safely from Point or Polygon.

        Never raises: non-numeric or ragged upstream coordinates fall back
        to (0.0, 0.0), which the service filters as "no position".
        """

        def _pair(a, b) -> tuple[float, float] | None:
            try:
                return (float(a), float(b))
            except (TypeError, ValueError):
                return None

        coords = self.coordinates
        if not isinstance(coords, list) or not coords:
            return (0.0, 0.0)
        first = coords[0]
        if isinstance(first, (int, float)) and len(coords) >= 2:
            return _pair(coords[0], coords[1]) or (0.0, 0.0)
        if isinstance(first, list) and first:
            inner = first[0]
            if isinstance(inner, (int, float)) and len(first) >= 2:
                return _pair(first[0], first[1]) or (0.0, 0.0)
            if isinstance(inner, list) and len(inner) >= 2:
                # Polygon ring: first position of the first ring.
                ring = inner[0] if inner and isinstance(inner[0], list) else inner
                if isinstance(ring, list) and len(ring) >= 2:
                    return _pair(ring[0], ring[1]) or (0.0, 0.0)
        return (0.0, 0.0)


class EonetEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")
    id: str
    title: str
    description: str | None = None
    link: str = ""
    categories: list[EonetCategory] = Field(default_factory=list)
    geometry: list[EonetGeometry] = Field(default_factory=list)

    # Stable EONET category ids (exact match first — substring matching
    # misfires on future categories, e.g. "campfire" containing "fire").
    _EONET_TYPE_BY_ID = {
        "wildfires": "wildfire",
        "severeStorms": "storm",
        "volcanoes": "volcano",
        "floods": "flood",
        "earthquakes": "earthquake",
        "seaLakeIce": "disaster",
        "drought": "disaster",
        "dustHaze": "disaster",
        "landslides": "disaster",
        "manmade": "disaster",
        "snow": "disaster",
        "tempExtremes": "disaster",
        "waterColor": "disaster",
    }

    @computed_field
    @property
    def hazard_type(
        self,
    ) -> Literal["wildfire", "storm", "volcano", "flood", "earthquake", "disaster"]:
        for c in self.categories:
            mapped = self._EONET_TYPE_BY_ID.get(c.id)
            if mapped is not None:
                return mapped  # type: ignore[return-value]
        # Fallback for unknown future ids: conservative substring scan on the
        # title only (ids are the stable contract; titles are display text).
        titles = " ".join(c.title.lower() for c in self.categories)
        if "wildfire" in titles:
            return "wildfire"
        if "volcano" in titles:
            return "volcano"
        if "flood" in titles:
            return "flood"
        if "storm" in titles or "cyclone" in titles or "hurricane" in titles:
            return "storm"
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
