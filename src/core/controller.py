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
        self.page.fonts = {}
        self.page.theme = AppTheme.get_light_theme()
        self.page.dark_theme = AppTheme.get_dark_theme()
        self.page.theme.font_family = "Outfit"
        self.page.dark_theme.font_family = "Outfit"
        self.page.theme_mode = ft.ThemeMode.SYSTEM
        self.page.window.min_width = 360
        self.page.window.min_height = 600

        is_web = getattr(self.page, "web", False)

        # Register Native Ecosystem Services (Desktop / Mobile only)
        if not is_web:
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
        else:
            state.is_online = True

        self.storage = StorageService(self.page)
        self.ad_service = AdService(self.page)
        state.ad_service = self.ad_service

        # Load Saved Settings
        await self._load_saved_state()

        # UMP GDPR Consent & Preload Interstitial Ads on mobile
        if not is_web:
            self.page.run_task(self.ad_service.gather_consent)
            self.page.run_task(self.ad_service.preload_interstitial)

        # Initial Telemetry Load
        self.page.run_task(self.refresh_all)

        # Live-monitor cadence — keep feeds fresh without manual refreshes
        self._telemetry_task = asyncio.create_task(self._telemetry_loop())

        # Mount React-style Component Tree
        from app_shell import AppShell

        methods = ControllerMethods(
            refresh_all=self.refresh_all,
            select_coordinates=self.select_coordinates,
            locate_user=self.locate_user,
            save_setting=self.save_setting,
            toggle_bookmark=self.toggle_bookmark,
            open_report=self.open_report,
            share_text=self.share_text,
            launch_url=self.launch_external_url,
            fetch_radius_history=SeismicService.fetch_radius_history,
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
            if onboarding_done == "true" or self.page.web:
                state.has_accepted_terms = True
                state.is_first_launch = False

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
            if self._controller_methods and self._controller_methods.set_theme_mode:
                self._controller_methods.set_theme_mode(self.page.theme_mode)
            self.page.update()

    _refresh_lock: asyncio.Lock | None = None
    _telemetry_task: asyncio.Task | None = None
    _TELEMETRY_REFRESH_SECONDS = 300  # 5 min — USGS/EONET update upstream

    async def _telemetry_loop(self) -> None:
        """Periodic telemetry cadence so the app reads like a live monitor."""
        while True:
            await asyncio.sleep(self._TELEMETRY_REFRESH_SECONDS)
            try:
                await self.refresh_all()
            except Exception as ex:
                logger.debug("Periodic telemetry refresh skipped: %s", ex)

    def shutdown(self) -> None:
        """Cancel the periodic telemetry loop on app close."""
        if self._telemetry_task and not self._telemetry_task.done():
            self._telemetry_task.cancel()

    async def refresh_all(self) -> None:
        """Fetch real-time USGS earthquakes, NASA disasters, atmospheric telemetry, and space weather."""
        if not state.is_online:
            logger.info(
                "Telemetry fetch skipped: Device is offline. Using local cache."
            )
            return
        if self._refresh_lock is None:
            self._refresh_lock = asyncio.Lock()
        if self._refresh_lock.locked():
            logger.info("Refresh already in progress — throttling duplicate call")
            return
        async with self._refresh_lock:
            await self._do_refresh()

    async def _do_refresh(self) -> None:
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

            # Fetch all global data concurrently (category-aware disasters)
            eq_task = SeismicService.fetch_earthquakes(state.min_magnitude_filter)
            dis_task = DisasterService.fetch_active_disasters(
                state.selected_hazard_type
            )
            atmo_task = AtmosphericService.fetch_location_telemetry(
                state.current_lat, state.current_lon
            )
            space_task = SpaceWeatherService.fetch_space_weather()

            results = await asyncio.gather(
                eq_task,
                dis_task,
                atmo_task,
                space_task,
                return_exceptions=True,
            )

            if isinstance(results[0], list):
                state.earthquakes = results[0]
            if isinstance(results[1], list):
                state.disasters = results[1]
            if isinstance(results[2], dict) and results[2]:
                atmo = results[2]
                state.weather_data = atmo.get("weather", {})
                state.air_quality_data = atmo.get("air_quality", {})
                state.flood_data = atmo.get("flood", {})
                state.marine_data = atmo.get("marine", {})
            if isinstance(results[3], dict) and results[3]:
                state.space_weather = results[3]

            # Cache local telemetry envelope
            if self.storage:
                payload = {
                    "weather": state.weather_data,
                    "air_quality": state.air_quality_data,
                    "flood": state.flood_data,
                    "marine": state.marine_data,
                }
                await self.storage.set_cached_telemetry(
                    cache_key, payload, ttl_seconds=300.0
                )

            state.telemetry_version += 1
            logger.info("All planetary telemetry feeds updated successfully")
            if self.page:
                self.page.update()

        except Exception:
            logger.exception("Telemetry refresh failed")
            show_snack(self.page, ERR_GENERIC, bgcolor=AppColors.ERROR)
        finally:
            state.is_loading = False
            if self.page:
                self.page.update()

    async def select_coordinates(
        self, lat: float, lon: float, name: str, country: str = ""
    ) -> None:
        """Update active focus point and fetch hyper-local telemetry."""
        state.current_lat = lat
        state.current_lon = lon
        state.current_location_name = name
        state.current_country = country
        # Visible confirmation — the observable writes re-render every screen,
        # but the user still needs an explicit "this happened" signal.
        show_snack(self.page, f"Now tracking: {name}", bgcolor=AppColors.SUCCESS)

        if self.ad_service:
            with contextlib.suppress(Exception):
                await self.ad_service.show_interstitial(min_interval_seconds=120.0)

        if self.haptics:
            with contextlib.suppress(Exception):
                await self.haptics.selection_click()

        if self.storage:
            recent = list(state.recent_searches)
            entry = {"name": name, "country": country, "lat": lat, "lon": lon}
            if entry in recent:
                recent.remove(entry)
            recent.insert(0, entry)
            state.recent_searches = recent[:10]
            await self.storage.set(STORAGE_RECENT_SEARCHES, state.recent_searches)

        # Fetch elevation for the new focus (non-blocking, logged)
        try:
            from services.geocoding_service import GeocodingService

            elev = await GeocodingService.get_elevation(lat, lon)
            if elev:
                state.current_elevation = elev
        except Exception:
            pass

        if self.page:
            self.page.update()

        await self.refresh_all()

    async def open_report(self) -> None:
        """Open Situation Report with strategic interstitial transition on mobile."""
        if self.ad_service:
            with contextlib.suppress(Exception):
                await self.ad_service.show_interstitial(min_interval_seconds=60.0)
        if self._controller_methods and self._controller_methods.show_report:
            self._controller_methods.show_report()

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
            state.bookmarks = [*state.bookmarks, location]
            show_snack(
                self.page, f"Saved '{name}' to bookmarks", bgcolor=AppColors.SUCCESS
            )

        if self.storage:
            await self.storage.set(STORAGE_BOOKMARKS, state.bookmarks)
        state.telemetry_version += 1

    async def locate_user(self) -> None:
        """Locate user using native GPS with universal IP fallback and reverse geocoding."""
        await DeviceServices.locate_user(
            self.geolocator,
            self.page,
            lambda lat, lon, name, country: self.select_coordinates(
                lat, lon, name, country
            ),
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
