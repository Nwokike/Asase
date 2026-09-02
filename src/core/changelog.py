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
}


def notes_for(version: str) -> str:
    """Changelog entry for a version, falling back to the latest entry."""
    return CHANGELOG.get(version) or next(reversed(CHANGELOG.values()), "")
