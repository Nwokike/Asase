"""AppController — Business logic, native service management, and telemetry orchestration."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

import flet as ft
from flet_geolocator import Geolocator

from core.constants import (
    APP_NAME,
    APP_VERSION,
    ERR_GENERIC,
    MSG_OFFLINE,
    MSG_ONLINE,
    STORAGE_BOOKMARKS,
    STORAGE_MIN_MAGNITUDE,
    STORAGE_ONBOARDING_DONE,
    STORAGE_RECENT_SEARCHES,
    STORAGE_SPEED_UNIT,
    STORAGE_TEMP_UNIT,
    STORAGE_THEME,
)
from core.device_services import DeviceServices
from core.network import NetworkManager
from core.notify import show_snack
from core.state import state
from core.theme import AppColors, AppTheme
from services.ad_service import AdService
from services.atmospheric_service import AtmosphericService
from services.disaster_service import DisasterService
from services.geocoding_service import GeocodingService
from services.seismic_service import SeismicService
from services.space_weather_service import SpaceWeatherService
from services.storage_service import StorageService
from state.controller_ctx import ControllerMethods, ControllerMethodsCtx

logger = logging.getLogger("asase.controller")


class AppController:
    """Top-level application controller managing telemetry services, persistence, and state."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.storage: StorageService | None = None
        self.ad_service: AdService | None = None
        self.connectivity: ft.Connectivity | None = None
        self.geolocator: Geolocator | None = None
        self.haptics: ft.HapticFeedback | None = None
        self.share: ft.Share | None = None
        self.url_launcher: ft.UrlLauncher | None = None
        self.storage_paths: ft.StoragePaths | None = None
        self._controller_methods: ControllerMethods | None = None

    async def init(self) -> None:
        """Initialize page configuration, services, storage, and mount AppShell."""
        logger.info("Starting %s v%s Earth Intelligence", APP_NAME, APP_VERSION)

        self.page.title = f"{APP_NAME} — Earth Intelligence"
        self.page.padding = 0
        self.page.spacing = 0
        self.page.fonts = {
            "Outfit": (
                "https://fonts.googleapis.com/css2?"
                "family=Outfit:wght@300;400;500;600;700&display=swap"
            )
        }
        self.page.theme = AppTheme.get_light_theme()
        self.page.dark_theme = AppTheme.get_dark_theme()
        self.page.theme.font_family = "Outfit"
        self.page.dark_theme.font_family = "Outfit"
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.window.min_width = 360
        self.page.window.min_height = 600

        # Register Native Ecosystem Services
        self.connectivity = ft.Connectivity()
        self.connectivity.on_change = self._on_connectivity_change
        self.page.services.append(self.connectivity)
        self.page.run_task(self._init_connectivity)
        self.page.on_app_lifecycle_state_change = self._on_lifecycle_change

        self.geolocator = Geolocator()
        self.page.services.append(self.geolocator)

        self.haptics = ft.HapticFeedback()
        self.page.services.append(self.haptics)

        self.share = ft.Share()
        self.page.services.append(self.share)

        self.url_launcher = ft.UrlLauncher()
        self.page.services.append(self.url_launcher)

        self.storage_paths = ft.StoragePaths()
        self.page.services.append(self.storage_paths)

        self.storage = StorageService(self.page)
        self.ad_service = AdService(self.page)

        # Load Saved Settings
        await self._load_saved_state()

        # Preload Interstitial Ads & Consent on mobile
        self.page.run_task(self.ad_service.preload_interstitial)

        # Initial Telemetry Load
        self.page.run_task(self.refresh_all)

        # Mount React-style Component Tree
        from app_shell import AppShell

        methods = ControllerMethods(
            refresh_all=self.refresh_all,
            select_coordinates=self.select_coordinates,
            locate_user=self.locate_user,
            save_setting=self.save_setting,
            toggle_bookmark=self.toggle_bookmark,
            share_text=self.share_text,
            launch_url=self.launch_external_url,
        )
        self._controller_methods = methods
        self.page.render(lambda: ControllerMethodsCtx(methods, lambda: AppShell()))
        logger.info("Asase AppShell mounted successfully")

    async def _load_saved_state(self) -> None:
        """Load stored user preferences and recent history."""
        if not self.storage:
            return
        try:
            saved_theme = await self.storage.get(STORAGE_THEME)
            if saved_theme == "dark":
                self.page.theme_mode = ft.ThemeMode.DARK
            elif saved_theme == "light":
                self.page.theme_mode = ft.ThemeMode.LIGHT
            else:
                self.page.theme_mode = ft.ThemeMode.SYSTEM
            state.theme_mode = self.page.theme_mode

            min_mag = await self.storage.get(STORAGE_MIN_MAGNITUDE)
            if min_mag is not None:
                state.min_magnitude_filter = float(min_mag)

            temp_u = await self.storage.get(STORAGE_TEMP_UNIT)
            if temp_u:
                state.temp_unit = temp_u

            speed_u = await self.storage.get(STORAGE_SPEED_UNIT)
            if speed_u:
                state.speed_unit = speed_u

            onboarding_done = await self.storage.get(STORAGE_ONBOARDING_DONE)
            if onboarding_done == "true":
                state.has_accepted_terms = True

            saved_bookmarks = await self.storage.get(STORAGE_BOOKMARKS)
            if isinstance(saved_bookmarks, list):
                state.bookmarks = saved_bookmarks

            recent = await self.storage.get(STORAGE_RECENT_SEARCHES)
            if isinstance(recent, list):
                state.recent_searches = recent

        except Exception as e:
            logger.warning("Failed to load saved state: %s", e)

    async def save_setting(self, key: str, value: Any) -> None:
        """Persist a setting key-value pair and reactively update state."""
        if self.storage:
            await self.storage.set(key, value)
        if key == STORAGE_THEME and self.page:
            if value == "dark":
                self.page.theme_mode = ft.ThemeMode.DARK
            elif value == "light":
                self.page.theme_mode = ft.ThemeMode.LIGHT
            else:
                self.page.theme_mode = ft.ThemeMode.SYSTEM
            state.theme_mode = self.page.theme_mode
            state.theme_version += 1
            state.telemetry_version += 1
            self.page.update()

    async def refresh_all(self) -> None:
        """Fetch real-time USGS earthquakes, NASA disasters, atmospheric telemetry, and space weather."""
        if not state.is_online:
            logger.info(
                "Telemetry fetch skipped: Device is offline. Using local cache."
            )
            return

        state.is_loading = True
        logger.info(
            "Refreshing all planetary telemetry feeds via NetworkManager pool..."
        )

        try:
            cache_key = f"telemetry_{state.current_lat:.2f}_{state.current_lon:.2f}"
            cached = None
            if self.storage:
                cached = await self.storage.get_cached_telemetry(cache_key)

            if cached:
                logger.info(
                    "Using fresh cached telemetry envelope for (%s, %s)",
                    state.current_lat,
                    state.current_lon,
                )
                state.weather_data = cached.get("weather", {})
                state.air_quality_data = cached.get("air_quality", {})
                state.flood_data = cached.get("flood", {})
                state.marine_data = cached.get("marine", {})

            # Fetch all global data concurrently
            eq_task = SeismicService.fetch_earthquakes(state.min_magnitude_filter)
            dis_task = DisasterService.fetch_active_disasters()
            weather_task = AtmosphericService.fetch_weather_forecast(
                state.current_lat, state.current_lon
            )
            aq_task = AtmosphericService.fetch_air_quality(
                state.current_lat, state.current_lon
            )
            flood_task = AtmosphericService.fetch_river_discharge(
                state.current_lat, state.current_lon
            )
            marine_task = AtmosphericService.fetch_marine_forecast(
                state.current_lat, state.current_lon
            )
            space_task = SpaceWeatherService.fetch_space_weather_summary()

            results = await asyncio.gather(
                eq_task,
                dis_task,
                weather_task,
                aq_task,
                flood_task,
                marine_task,
                space_task,
                return_exceptions=True,
            )

            if isinstance(results[0], list):
                state.earthquakes = results[0]
            if isinstance(results[1], list):
                state.disasters = results[1]
            if isinstance(results[2], dict) and results[2]:
                state.weather_data = results[2]
            if isinstance(results[3], dict) and results[3]:
                state.air_quality_data = results[3]
            if isinstance(results[4], dict) and results[4]:
                state.flood_data = results[4]
            if isinstance(results[5], dict) and results[5]:
                state.marine_data = results[5]
            if isinstance(results[6], dict) and results[6]:
                state.space_weather = results[6]

            # Cache local telemetry envelope
            if self.storage:
                payload = {
                    "weather": state.weather_data,
                    "air_quality": state.air_quality_data,
                    "flood": state.flood_data,
                    "marine": state.marine_data,
                }
                await self.storage.set_cached_telemetry(cache_key, payload, ttl=300)

            state.telemetry_version += 1
            logger.info("All planetary telemetry feeds updated successfully")

        except Exception:
            logger.exception("Telemetry refresh failed")
            show_snack(self.page, ERR_GENERIC, bgcolor=AppColors.ERROR)
        finally:
            state.is_loading = False

    async def select_coordinates(
        self, lat: float, lon: float, name: str, country: str = ""
    ) -> None:
        """Update active focus point and fetch hyper-local telemetry."""
        state.current_lat = lat
        state.current_lon = lon
        state.current_location_name = name
        state.current_country = country

        if self.haptics:
            with contextlib.suppress(Exception):
                await self.haptics.selection_click()

        elev = await GeocodingService.get_elevation(lat, lon)
        state.current_elevation = elev

        entry = {
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "country": country,
        }
        state.recent_searches = [
            e for e in state.recent_searches if e.get("name") != name
        ]
        state.recent_searches.insert(0, entry)
        state.recent_searches = state.recent_searches[:20]
        if self.storage:
            await self.storage.set(STORAGE_RECENT_SEARCHES, state.recent_searches)

        await self.refresh_all()

    async def toggle_bookmark(self, location: dict) -> None:
        """Toggle bookmark for a location dictionary with haptic feedback."""
        name = location.get("name")
        if not name:
            return

        if self.haptics:
            with contextlib.suppress(Exception):
                await self.haptics.selection_click()

        exists = any(b.get("name") == name for b in state.bookmarks)
        if exists:
            state.bookmarks = [b for b in state.bookmarks if b.get("name") != name]
            show_snack(
                self.page, f"Removed '{name}' from bookmarks", bgcolor=AppColors.GREY
            )
        else:
            state.bookmarks.append(location)
            show_snack(
                self.page, f"Saved '{name}' to bookmarks", bgcolor=AppColors.SUCCESS
            )

        if self.storage:
            await self.storage.set(STORAGE_BOOKMARKS, state.bookmarks)
        state.telemetry_version += 1

    async def locate_user(self) -> None:
        """Locate user using native device GPS with permission handling."""
        await DeviceServices.locate_user(
            self.geolocator,
            self.page,
            lambda lat, lon: self.select_coordinates(lat, lon, "My GPS Location", ""),
        )

    async def share_text(self, text: str, subject: str = "Planetary Alert") -> None:
        """Share text or report using native OS Share sheet."""
        await DeviceServices.share_text(self.share, self.page, text, subject)

    async def launch_external_url(self, url: str) -> None:
        """Launch web link in external browser or custom tab."""
        await DeviceServices.launch_url(self.url_launcher, url)

    # ── Connectivity & Lifecycle ──

    async def _init_connectivity(self) -> None:
        if not self.connectivity:
            return
        try:
            res = await self.connectivity.get_connectivity()
            types = res if isinstance(res, list) else [res]
            state.is_online = ft.ConnectivityType.NONE not in types
        except Exception:
            pass

    def _on_connectivity_change(self, e) -> None:
        was_online = state.is_online
        try:
            raw = getattr(e, "connectivity", None) or getattr(e, "data", None)
            types = raw if isinstance(raw, list) else [raw]
            state.is_online = ft.ConnectivityType.NONE not in types
        except Exception:
            return
        if was_online and not state.is_online:
            logger.warning("Connectivity lost — switched to offline telemetry cache")
            show_snack(self.page, MSG_OFFLINE, duration=8000)
        elif not was_online and state.is_online:
            logger.info("Connectivity restored — live telemetry active")
            show_snack(self.page, MSG_ONLINE, bgcolor=AppColors.SUCCESS)
            self.page.run_task(self.refresh_all)

    async def _on_lifecycle_change(self, e: ft.AppLifecycleStateChangeEvent) -> None:
        if (
            e.state in (ft.AppLifecycleState.RESUME, ft.AppLifecycleState.SHOW)
            and self.connectivity
        ):
            try:
                res = await self.connectivity.get_connectivity()
                types = res if isinstance(res, list) else [res]
                state.is_online = ft.ConnectivityType.NONE not in types
            except Exception:
                pass

    def on_error(self, e) -> None:
        logger.error("Page uncaught error: %s", e.data)
        show_snack(self.page, ERR_GENERIC, bgcolor=AppColors.ERROR)

    async def cleanup(self) -> None:
        """Gracefully release HTTP connection pools."""
        await NetworkManager.close_all()
