"""Constants and API endpoints for Asase Earth Intelligence."""

from __future__ import annotations

APP_NAME = "Asase"
APP_VERSION = "1.0.0"
APP_SUBTITLE = "Global Earth Intelligence & Planetary Telemetry"

# Kiri Gateway (family-shared app key, same as akili/MarkItDown)
GATEWAY_BASE_URL = "https://api.kiri.ng"
GATEWAY_CHAT_URL = f"{GATEWAY_BASE_URL}/chat"
GATEWAY_APP_SECRET = "mobile-v1"

# Storage Keys (Prefix: asase.)
STORAGE_THEME = "asase.theme"
STORAGE_TEMP_UNIT = "asase.temp_unit"  # celsius | fahrenheit
STORAGE_SPEED_UNIT = "asase.speed_unit"  # kmh | mph | ms
STORAGE_MIN_MAGNITUDE = "asase.min_magnitude"  # float (e.g. 2.5)
STORAGE_BOOKMARKS = "asase.bookmarks"
STORAGE_RECENT_SEARCHES = "asase.recent_searches"
STORAGE_OFFLINE_CACHE = "asase.offline_cache"
STORAGE_ONBOARDING_DONE = "asase.onboarding_done"

# UI Messages
MSG_OFFLINE = "Offline Mode: Displaying cached planetary intelligence data."
MSG_ONLINE = "Connection restored. Live telemetry stream active."
MSG_SEARCH_OFFLINE = "Device is offline. Showing cached report."
ERR_GENERIC = "An unexpected error occurred while fetching earth telemetry."
ERR_NETWORK = "Network timeout. Could not reach planetary data servers."

# Free & Public API Endpoints (100% Auth-Free)
USGS_EARTHQUAKES_HOUR = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
)
USGS_EARTHQUAKES_DAY = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
)
USGS_EARTHQUAKES_SIGNIFICANT = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"

NASA_EONET_EVENTS = "https://eonet.gsfc.nasa.gov/api/v3/events?status=open&limit=100"
EONET_CATEGORY_MAP = {
    "wildfire": "wildfires",
    "fire": "wildfires",
    "flood": "floods",
    "storm": "severeStorms",
    "volcano": "volcanoes",
    "earthquake": "earthquakes",
}

GDACS_ALERTS_RSS = "https://www.gdacs.org/xml/rss.xml"

OPEN_METEO_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_AIR_QUALITY = "https://air-quality-api.open-meteo.com/v1/air-quality"
OPEN_METEO_FLOOD = "https://flood-api.open-meteo.com/v1/flood"
OPEN_METEO_MARINE = "https://marine-api.open-meteo.com/v1/marine"
OPEN_METEO_ELEVATION = "https://api.open-meteo.com/v1/elevation"

NOAA_SWPC_KP_INDEX = (
    "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
)
NOAA_SWPC_KP_FORECAST = (
    "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
)
NOAA_SWPC_SOLAR_FLARES = (
    "https://services.swpc.noaa.gov/json/goes/primary/xrays-6-hour.json"
)
