"""NASA EONET and GDACS disaster schemas — stdlib dataclasses, no pydantic."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Literal

from models._coerce import opt_list, opt_str
from models._model import DataModel, parse_models


@dataclass(frozen=True, kw_only=True)
class EonetCategory(DataModel):
    id: str
    title: str

    @classmethod
    def model_validate(cls, data) -> EonetCategory:
        if not isinstance(data, dict):
            raise TypeError("EonetCategory: expected object")
        return cls(id=opt_str(data, "id", ""), title=opt_str(data, "title", ""))


@dataclass(frozen=True, kw_only=True)
class EonetGeometry(DataModel):
    date: str = ""
    type: str = "Point"
    coordinates: list = field(default_factory=list)

    @classmethod
    def model_validate(cls, data) -> EonetGeometry:
        if not isinstance(data, dict):
            raise TypeError("EonetGeometry: expected object")
        return cls(
            date=opt_str(data, "date", ""),
            coordinates=opt_list(data, "coordinates"),
        )

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


@dataclass(frozen=True, kw_only=True)
class EonetEvent(DataModel):
    _COMPUTED = ("hazard_type", "primary_coordinates")

    id: str
    title: str
    description: str | None = None
    link: str = ""
    categories: list[EonetCategory] = field(default_factory=list)
    geometry: list[EonetGeometry] = field(default_factory=list)

    # Stable EONET category ids (exact match first — substring matching
    # misfires on future categories, e.g. "campfire" containing "fire").
    _EONET_TYPE_BY_ID: ClassVar[dict] = {
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

    @classmethod
    def model_validate(cls, data) -> EonetEvent:
        if not isinstance(data, dict):
            raise TypeError("EonetEvent: expected object")
        # id/title are the required pair: a record without either is the
        # "missing required shape" case the fail-open tests pin down.
        event_id = data.get("id")
        title = data.get("title")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("EonetEvent: id required")
        if not isinstance(title, str) or not title:
            raise ValueError("EonetEvent: title required")
        description = data.get("description")
        if description is not None and not isinstance(description, str):
            raise ValueError("description: expected string")
        return cls(
            id=event_id,
            title=title,
            description=description,
            link=opt_str(data, "link", ""),
            categories=parse_models(data, "categories", EonetCategory.model_validate),
            geometry=parse_models(data, "geometry", EonetGeometry.model_validate),
        )

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

    @property
    def primary_coordinates(self) -> tuple[float, float]:
        if not self.geometry:
            return (0.0, 0.0)
        return self.geometry[-1].point_coords

    @property
    def polygon_ring(self) -> list[list[float]] | None:
        """Outer ring of the latest Polygon geometry, if any.

        Returns [[lon, lat], ...] with ≥3 valid positions, else None.
        Point geometries (and degenerate rings) yield None — callers keep
        the point marker as fallback.
        """
        if not self.geometry:
            return None
        coords = self.geometry[-1].coordinates
        if not isinstance(coords, list) or not coords:
            return None
        first = coords[0]
        # Polygon: [[[lon, lat], ...]] — outer ring is coords[0].
        ring = (
            first
            if isinstance(first, list) and first and isinstance(first[0], list)
            else None
        )
        if ring is None:
            return None
        cleaned: list[list[float]] = []
        for pt in ring:
            try:
                if isinstance(pt, list) and len(pt) >= 2:
                    cleaned.append([float(pt[0]), float(pt[1])])
            except (TypeError, ValueError):
                continue
        return cleaned if len(cleaned) >= 3 else None

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
            "polygon_ring": self.polygon_ring,
            "url": self.link,
            "type": self.hazard_type,
        }


@dataclass(frozen=True, kw_only=True)
class EonetResponse(DataModel):
    title: str = ""
    events: list[EonetEvent] = field(default_factory=list)

    @classmethod
    def model_validate(cls, data) -> EonetResponse:
        if not isinstance(data, dict):
            raise TypeError("EonetResponse: expected object")
        return cls(
            title=opt_str(data, "title", ""),
            events=parse_models(data, "events", EonetEvent.model_validate),
        )
