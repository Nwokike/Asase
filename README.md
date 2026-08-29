# 🌍 Asase — Global Earth Intelligence & Planetary Defense OS

**Asase** is a cross-platform Planetary Intelligence & Multi-Hazard Telemetry application built with [Flet](https://flet.dev). It aggregates real-time public-domain geophysical, meteorological, and space-weather data into a unified, responsive command center.

---

## 🚀 Planetary Telemetry Feeds (100% Free & No-Auth)

- 🔴 **USGS Seismic Radar**: Real-time global earthquake feeds (Richter magnitude, focal depth, tsunami alerts, modified Mercalli intensity).
- 🟠 **NASA EONET & GDACS Disaster Monitor**: Satellite thermal anomaly tracking for active wildfires, volcanic eruptions, tropical cyclones, and UN emergency alerts.
- 🔵 **Open-Meteo Atmospheric & Climate Suite**:
  - **Hyperlocal Weather**: Temperature, surface pressure, extreme wind gusts, and **CAPE** (Convective Available Potential Energy) thunderstorm index.
  - **Global Air Quality (AQI)**: Real-time US & European AQI, $PM_{2.5}$, $PM_{10}$, Carbon Monoxide ($CO$), Ozone ($O_3$), $NO_2$, and Saharan dust concentration.
  - **GloFAS Hydrology Engine**: 10-day global river discharge forecasting and recurrence flood risk levels (2-year, 5-year, 20-year return periods).
  - **Marine & Ocean Dynamics**: Swell wave height, period, and coastal storm surge risks.
- 🟣 **NOAA SWPC Space Weather**: Real-time planetary $K_p$-index geomagnetic storm monitor and solar radiation flare tracking.

---

## 💎 Core Capabilities & Architecture

- **Unified Responsive Interface**: One single codebase for Web, Android, and Desktop. Fluid multi-column telemetry grid and full-bleed maps on widescreen/desktop, cleanly stacked on mobile.
- **Interactive Multi-Layer Map**: Powered by `flet-map` with Dark CartoDB tiles and live pulsing hazard markers.
- **Resilient Offline Architecture**: Crash-proof storage with atomic file writing, backup rotation (`.json.bak`), and corruption recovery across Desktop/Android and Web `client_storage`.
- **Live Diagnostics Terminal**: In-memory ring-buffer activity terminal (`MemoryLogHandler`) embedded in Settings with one-tap log export.
- **Monetization & Privacy**: Built-in Google AdMob banner and interstitial ads with full privacy consent.

---

## 🛠️ Development & Testing

```bash
# Install dependencies
uv sync --dev

# Run linter & formatter
uv run ruff check . --fix
uv run ruff format .

# Run test suite
uv run pytest -v

# Start the application
uv run flet run
```

---

## 🧭 License

MIT License © 2026 Kiri Research Labs
