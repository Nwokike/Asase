"""Observable Application State for Asase Earth Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import flet as ft


@dataclass
class AppState:
    # Network & Lifecycle
    is_online: bool = True
    is_loading: bool = False
    loading_message: str = "Updating planetary telemetry..."
    is_first_launch: bool = True
    has_accepted_terms: bool = False
    theme_mode: ft.ThemeMode = ft.ThemeMode.SYSTEM

    # Geolocation / Active Focus Point (Defaults to Global / Accra/Lagos/Nairobi or User GPS)
    current_location_name: str = "Global Telemetry"
    current_country: str = ""
    current_lat: float = 6.5244
    current_lon: float = 3.3792
    current_elevation: float = 10.0

    # Live Hazards & Telemetry Feeds
    earthquakes: list[dict] = field(default_factory=list)
    disasters: list[dict] = field(default_factory=list)  # NASA EONET & GDACS
    weather_data: dict = field(default_factory=dict)
    air_quality_data: dict = field(default_factory=dict)
    flood_data: dict = field(default_factory=dict)
    marine_data: dict = field(default_factory=dict)
    space_weather: dict = field(default_factory=dict)

    # Local Persistence
    recent_searches: list[dict] = field(default_factory=list)
    bookmarks: list[dict] = field(default_factory=list)

    # User Preferences
    min_magnitude_filter: float = 2.5
    temp_unit: str = "celsius"  # celsius | fahrenheit
    speed_unit: str = "kmh"  # kmh | mph
    selected_hazard_type: str = "all"  # all | earthquake | fire | flood | storm

    # Detail Selection
    selected_marker: dict | None = None
    telemetry_version: int = 0
    theme_version: int = 0
    ad_service: Any = None


state = AppState()
