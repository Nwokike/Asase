"""Bundled changelog shown by the version dialog when the app is up to
date — works fully offline. One line per release; keep the entry for the
current APP_VERSION in sync when bumping."""

CHANGELOG: dict[str, str] = {
    "1.0.0": (
        "• Initial release: live USGS, NASA EONET, Open-Meteo & NOAA telemetry\n"
        "• Grounded AI briefings, multi-hazard map, adaptive dark/light mode"
    ),
    "1.0.1": (
        "• Accurate web location: real GPS only — no more estimated cities\n"
        "• Remembers your last tracked city between launches\n"
        "• Faster refresh: city switches refetch local feeds only\n"
        "• Web caching + simple theme-reactive onboarding & boot screen\n"
        "• In-app What's New dialog (mobile/desktop)"
    ),
    "1.0.2": (
        "• Faster refresh: unchanged feeds skip re-download (ETag caching)\n"
        "• New pollutant comparison chart in the air-quality dossier\n"
        "• Wildfire perimeters & hazard footprints drawn on the map\n"
        "• Temperature (°C/°F) and wind (km/h/mph) follow your settings\n"
        "• Reliability pass: feeds survive bad records, search + cache hardened"
    ),
}


def notes_for(version: str) -> str:
    """Changelog entry for a version, falling back to the latest entry."""
    return CHANGELOG.get(version) or next(reversed(CHANGELOG.values()), "")
