<p align="center">
  <img src="src/assets/logo.svg" alt="Asase Earth Intelligence" width="360" />
</p>

<p align="center">
  <strong>Global Earth Intelligence & Multi-Hazard Planetary Defense Platform</strong>
</p>

<p align="center">
  <a href="https://asase.kiri.ng"><img src="https://img.shields.io/badge/Web_App-asase.kiri.ng-00B0FF?style=for-the-badge&logo=google-chrome&logoColor=white" alt="Live Web App" /></a>
  <a href="https://play.google.com/store/apps/details?id=ng.kiri.asase"><img src="https://img.shields.io/badge/Google_Play-Android-3DDC84?style=for-the-badge&logo=google-play&logoColor=white" alt="Google Play Store" /></a>
  <a href="#download"><img src="https://img.shields.io/badge/Download_Windows_EXE-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows EXE" /></a>
  <a href="#download"><img src="https://img.shields.io/badge/Download_Linux_DEB-FCC624?style=for-the-badge&logo=linux&logoColor=black" alt="Linux DEB" /></a>
  <a href="#download"><img src="https://img.shields.io/badge/Download_Linux_RPM-E91E63?style=for-the-badge&logo=redhat&logoColor=white" alt="Linux RPM" /></a>
  <img src="https://img.shields.io/badge/Built_with-Flet_0.86-00B0FF?style=for-the-badge&logo=flutter&logoColor=white" alt="Flet" />
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
</p>

---

## 📥 Download

| Platform | Package | Description |
| :---: | :---: | :--- |
| 🌐 **Web App** | [![Live Web App](https://img.shields.io/badge/Launch-asase.kiri.ng-00B0FF?style=flat-square&logo=google-chrome&logoColor=white)](https://asase.kiri.ng) | Live progressive web application running directly in your browser |
| 🤖 **Android** | [![Play Store](https://img.shields.io/badge/Google_Play-414141?style=flat-square&logo=google-play&logoColor=white)](https://play.google.com/store/apps/details?id=ng.kiri.asase) | Recommended for Android mobile and tablet devices |
| 🪟 **Windows** | [![Windows Release](https://img.shields.io/badge/Download_Windows_Installer-0078D6?style=flat-square&logo=windows&logoColor=white)](https://github.com/Nwokike/Asase/releases/latest/download/Asase_Setup.exe) | Standalone Inno Setup installer with taskbar & desktop integration |
| 🐧 **Linux (Debian/Ubuntu)** | [![Linux DEB](https://img.shields.io/badge/Download_Linux_DEB-FCC624?style=flat-square&logo=linux&logoColor=black)](https://github.com/Nwokike/Asase/releases/latest/download/Asase_amd64.deb) | Native desktop package for Ubuntu, Debian, Linux Mint & Pop!_OS |
| 🎩 **Linux (Fedora/RHEL)** | [![Linux RPM](https://img.shields.io/badge/Download_Linux_RPM-E91E63?style=flat-square&logo=redhat&logoColor=white)](https://github.com/Nwokike/Asase/releases/latest/download/Asase_x86_64.rpm) | Native package for Fedora, openSUSE, RHEL & CentOS |
| 📦 **Linux (Universal)** | [![Linux TAR.GZ](https://img.shields.io/badge/Download_Linux_TAR.GZ-9C27B0?style=flat-square&logo=linux&logoColor=white)](https://github.com/Nwokike/Asase/releases/latest/download/Asase_linux_x86_64.tar.gz) | Standalone portable archive for Arch, Alpine, Steam Deck & all distros |

### Android Architecture Build Splits

| Variant | Download | Device Compatibility |
| :--- | :---: | :--- |
| 📱 **ARM64** (v8a) | [**asase-arm64-v8a.apk**](https://github.com/Nwokike/Asase/releases/latest/download/asase-arm64-v8a.apk) | Modern 64-bit Android smartphones & tablets |
| 📱 **ARMv7** (32-bit) | [**asase-armeabi-v7a.apk**](https://github.com/Nwokike/Asase/releases/latest/download/asase-armeabi-v7a.apk) | Legacy 32-bit Android devices |
| 💻 **x86_64** (Emulators) | [**asase-x86_64.apk**](https://github.com/Nwokike/Asase/releases/latest/download/asase-x86_64.apk) | ChromeOS, Chromebooks & Android desktop emulators |

---

## 🌍 Core Capabilities

| Capability | Telemetry Source | Description |
| :--- | :---: | :--- |
| **Seismic Hazards** | USGS FDSN | Real-time global earthquake feeds with Richter magnitude, depth, tsunami warnings, and geodesic shockwave radius. |
| **Space Weather & $K_p$** | NOAA SWPC | Planetary $K_p$-index geomagnetic disturbance monitor with 12-reading live progression curves. |
| **Solar Radiation** | NOAA GOES Primary | Real-time satellite solar X-ray flux and flare classification (A, B, C, M, X class). |
| **Atmospheric & Storms** | Open-Meteo Forecast | Hyperlocal temperature, surface pressure, extreme wind gusts, UV index, and CAPE thunderstorm potential. |
| **Air Quality Spectrum** | Open-Meteo AQI | European AQI, US AQI, $\text{PM}_{2.5}$, $\text{PM}_{10}$, Carbon Monoxide ($\text{CO}$), Ozone ($\text{O}_3$), $\text{NO}_2$, $\text{SO}_2$, and Saharan dust. |
| **GloFAS Hydrology** | Copernicus / GloFAS | Global river discharge forecasting ($m^3/s$) and 7-day hydrological flood progression. |
| **Marine Swell Dynamics** | Open-Meteo Marine | Ocean wave height, period, direction, and coastal swell surge risks. |
| **Planetary Disasters** | NASA EONET v3 | Satellite thermal anomaly tracking for active wildfires, severe storms, volcanoes, and sea ice. |

---

## 📸 Screenshots

### Radar Dashboard

<p align="center">
  <img src="screenshots/radar_home_mobile_light.png" width="90%" alt="Radar Dashboard — light mode" />
</p>
<p align="center"><em>Radar Dashboard — elevation, temperature, AQI & Kp-index chips for your pinned location, nearest-hazard warning, one-tap full dossier, and the live global hazard radar below</em></p>

<p align="center">
  <img src="screenshots/search_mobile_light.png" width="360" alt="Global place search" />
</p>
<p align="center"><em>Typeahead geocoding — search any city, region, or coordinate with live elevation and lat/lon results</em></p>

### Live Hazard Feeds

<table>
  <tr>
    <td width="50%"><img src="screenshots/seismic_feed_mobile_light.png" width="100%" alt="Recent seismic activity" /></td>
    <td width="50%"><img src="screenshots/wildfire_event_mobile_dark.png" width="100%" alt="Expanded wildfire event detail" /></td>
  </tr>
  <tr>
    <td align="center"><em>Recent seismic activity — USGS 24h feed with magnitude, depth, MMI, severity badges, and distance-from-you chips</em></td>
    <td align="center"><em>Tap a wildfire to expand inline — coordinates, view full dossier, share, and source attribution</em></td>
  </tr>
</table>

### Global Hazard Map

<table>
  <tr>
    <td width="50%"><img src="screenshots/full_map_mobile_light.png" width="100%" alt="Global hazard map — satellite view" /></td>
    <td width="50%"><img src="screenshots/full_map_event_mobile_dark.png" width="100%" alt="Selected earthquake on the map" /></td>
  </tr>
  <tr>
    <td align="center"><em>Satellite basemap with wildfire, seismic, and flood markers, proximity shockwave rings, and the AI Scan action</em></td>
    <td align="center"><em>Tap any marker to inspect the event — magnitude, depth, and one-tap full dossier right on the map</em></td>
  </tr>
</table>

### Space Weather & Location Intelligence

<table>
  <tr>
    <td width="50%"><img src="screenshots/space_weather_mobile_light.png" width="100%" alt="Space weather Kp-index and solar flux charts" /></td>
    <td width="50%"><img src="screenshots/risk_dossier_mobile_light.png" width="100%" alt="Location risk dossier with AI briefing" /></td>
  </tr>
  <tr>
    <td align="center"><em>Space weather — NOAA Kp-index with 12-reading progression and GOES solar X-ray flux live charts</em></td>
    <td align="center"><em>Location risk dossier — safety score, 5-axis multi-hazard threat radar, and the Kiri Intelligence AI briefing</em></td>
  </tr>
</table>

---

## ✨ Features

- **100% Free & Auth-Free** — Zero API keys required. Direct client connections to official open public domain planetary telemetry endpoints.
- **Watermark-Free Esri Dark Gray Map** — Auth-free Esri Dark Gray Canvas tiles with OpenStreetMap fallback and interactive shockwave circles.
- **Instant Reactive Theme Mode Switcher** — Real-time switching between **Light** ☀️, **Dark** 🌙, and **System** 🖥️ modes across all screens with transparent vector branding.
- **Hardware-Accelerated Charts** — Live geomagnetic curves and multi-axis planetary threat radar charts with `flet-charts`.
- **Proximity Geodesic Engine** — Haversine distance engine warning users of nearest active hazards (e.g. *"142 km from you"*).
- **Offline Telemetry Caching** — L1 LRU Memory + L2 Gzip Disk caching (`.json.gz`) with atomic swaps and corruption recovery.
- **Live Activity Terminal** — Real-time event and connection logging with one-tap clipboard copy and diagnostic inspection.
- **Native Sharing & Links** — 1-tap report sharing via `ft.Share` and official agency deep linking via `ft.UrlLauncher`.
- **Monetization & Privacy** — Responsive Google AdMob banners and interstitial ads with consent management.

---

## 🛠️ Development & Testing

```bash
# Install dependencies with uv
uv sync --dev

# Run linter & formatter checks
uv run ruff check . --fix
uv run ruff format .

# Run comprehensive test suite (51 tests)
uv run pytest -v

# Start local desktop development server
uv run flet run
```

---

## 🧭 License

MIT License © 2026 Kiri Research Labs. All planetary telemetry sourced from open public-domain science organizations (USGS, NOAA, NASA, Copernicus & Open-Meteo).
