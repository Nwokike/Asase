"""Asase — Main Entry Point and AppController."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

import flet as ft

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

logger = logging.getLogger("asase")


class AppController:
    """Top-level application controller managing telemetry services, persistence, and state."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.storage: StorageService | None = None
        self.ad_service: AdService | None = None
        self.connectivity: ft.Connectivity | None = None
        self.geolocator: ft.Geolocator | None = None
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

        # Register Services
        self.connectivity = ft.Connectivity()
        self.connectivity.on_change = self._on_connectivity_change
        self.page.services.append(self.connectivity)
        self.page.run_task(self._init_connectivity)
        self.page.on_app_lifecycle_state_change = self._on_lifecycle_change

        self.geolocator = ft.Geolocator()
        self.page.services.append(self.geolocator)

        self.storage = StorageService(self.page)
        self.ad_service = AdService(self.page)

        # Load Saved Settings
        await self._load_saved_state()

        # Preload Interstitial Ads on mobile
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
                state.is_first_launch = False

            recents = await self.storage.get(STORAGE_RECENT_SEARCHES)
            if recents and isinstance(recents, list):
                state.recent_searches = recents

            bookmarks = await self.storage.get(STORAGE_BOOKMARKS)
            if bookmarks and isinstance(bookmarks, list):
                state.bookmarks = bookmarks
        except Exception as e:
            logger.warning("Failed to load saved state: %s", e)

    async def save_setting(self, key: str, value: Any) -> None:
        """Persist a setting key-value pair."""
        if self.storage:
            await self.storage.set(key, value)

    async def refresh_all(self) -> None:
        """Fetch real-time USGS earthquakes, NASA disasters, atmospheric telemetry, and space weather."""
        if not state.is_online:
            logger.info(
                "Telemetry fetch skipped: Device is offline. Using local cache."
            )
            return

        state.is_loading = True
        logger.info("Refreshing all planetary telemetry feeds...")

        try:
            # Fetch all global data concurrently
            eq_task = SeismicService.fetch_earthquakes(state.min_magnitude_filter)
            dis_task = DisasterService.fetch_active_disasters()
            atm_task = AtmosphericService.fetch_location_telemetry(
                state.current_lat, state.current_lon
            )
            sw_task = SpaceWeatherService.fetch_space_weather()

            eqs, disasters, atm, space = await asyncio.gather(
                eq_task, dis_task, atm_task, sw_task, return_exceptions=True
            )

            if isinstance(eqs, list):
                state.earthquakes = eqs
            if isinstance(disasters, list):
                state.disasters = disasters
            if isinstance(atm, dict):
                state.weather_data = atm.get("weather", {})
                state.air_quality_data = atm.get("air_quality", {})
                state.flood_data = atm.get("flood", {})
                state.marine_data = atm.get("marine", {})
            if isinstance(space, dict):
                state.space_weather = space

            state.telemetry_version += 1
            logger.info("Planetary telemetry successfully synchronized")
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

        # Fetch elevation
        elev = await GeocodingService.get_elevation(lat, lon)
        state.current_elevation = elev

        # Record recent search
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

        # Refresh telemetry for new location
        await self.refresh_all()

    async def locate_user(self) -> None:
        """Locate user using device GPS coordinates."""
        if not self.geolocator:
            return
        try:
            logger.info("Requesting device GPS location...")
            pos = await self.geolocator.get_current_position()
            if pos:
                lat = float(pos.latitude)
                lon = float(pos.longitude)
                logger.info("GPS Coordinates resolved: (%s, %s)", lat, lon)
                await self.select_coordinates(lat, lon, "My GPS Location", "")
                show_snack(self.page, "GPS Location Updated", bgcolor=AppColors.SUCCESS)
        except Exception as ex:
            logger.warning("GPS Geolocation failed: %s", ex)
            show_snack(
                self.page,
                "Could not retrieve GPS location.",
                bgcolor=AppColors.WARNING,
            )

    # ── Connectivity & Lifecycle ──

    async def _init_connectivity(self) -> None:
        if not self.connectivity:
            return
        try:
            res = await self.connectivity.get_connectivity()
            state.is_online = ft.ConnectivityType.NONE not in res
        except Exception:
            pass

    def _on_connectivity_change(self, e) -> None:
        was_online = state.is_online
        try:
            types = getattr(e, "connectivity", None) or [e.data]
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
                state.is_online = ft.ConnectivityType.NONE not in res
            except Exception:
                pass

    def on_error(self, e) -> None:
        logger.error("Page uncaught error: %s", e.data)
        show_snack(self.page, ERR_GENERIC, bgcolor=AppColors.ERROR)


async def main(page: ft.Page) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    controller = AppController(page)
    await controller.init()
    page.on_error = controller.on_error

    async def _on_close(e=None):
        with contextlib.suppress(Exception):
            if controller.storage:
                await controller.storage.flush()
        with contextlib.suppress(Exception):
            if controller.ad_service:
                await controller.ad_service.close()

    page.on_close = _on_close
    page.on_disconnect = _on_close


if __name__ == "__main__":
    ft.run(main, assets_dir="src/assets")
