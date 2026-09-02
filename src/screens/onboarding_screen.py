"""OnboardingScreen — functional first-launch deck that works while it waits.

Modern web-pattern onboarding: the deck does real work instead of showing
marketing bullets. The controller's refresh_all already streams telemetry in
the background while onboarding is open — the deck surfaces that progress:

- Slide 1 (brand): logo + live "telemetry systems" progress panel
- Slide 2 (locality): debounced city search that pre-localizes feeds —
  select_coordinates fires immediately, so the dashboard opens localized
- Slide 3 (readiness): per-system Live/Syncing checklist; Enter Planetary
  Command always lands on an instant, ready dashboard

@ft.component — reads/writes observable state via AppStateCtx.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging

import flet as ft
from flet import Control

from components.home.location_search_bar import build_location_search_bar
from core import tokens
from core.constants import STORAGE_ONBOARDING_DONE
from core.state import state as app_state
from core.theme import AppColors, AppStyles, build_logo
from hooks.use_debounce import use_debounce
from services.geocoding_service import GeocodingService
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.onboarding")

_HERO_ICON = 56  # family-standard onboarding hero icon size (Sherlock ICON_FEATURE)
_SYSTEMS = [
    ("Seismic Network", "earthquakes"),
    ("Hazard Watch", "disasters"),
    ("Atmosphere", "weather_data"),
    ("Space Weather", "space_weather"),
]


def _is_live(field: str) -> bool:
    """A telemetry system is live when its observable feed has data."""
    return bool(getattr(app_state, field, None))


def _systems_ready() -> int:
    return sum(1 for _, f in _SYSTEMS if _is_live(f))


def _sys_row(label: str, ready: bool) -> ft.Control:
    return ft.Row(
        [
            ft.Icon(
                (
                    ft.Icons.CHECK_CIRCLE_ROUNDED
                    if ready
                    else ft.Icons.RADIO_BUTTON_UNCHECKED_ROUNDED
                ),
                size=tokens.ICON_SM,
                color=AppColors.PRIMARY if ready else ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Text(
                label,
                size=tokens.FONT_SM,
                weight=ft.FontWeight.W_500,
                color=ft.Colors.ON_SURFACE if ready else ft.Colors.ON_SURFACE_VARIANT,
                expand=True,
            ),
            ft.Text(
                "Live" if ready else "Syncing",
                size=tokens.FONT_XS,
                color=AppColors.PRIMARY if ready else ft.Colors.ON_SURFACE_VARIANT,
                weight=ft.FontWeight.W_600,
            ),
        ],
        spacing=tokens.SPACE_MD,
    )


def _hero_icon(icon, color: str, ready: bool = True) -> ft.Container:
    return ft.Container(
        content=ft.Icon(
            icon,
            size=_HERO_ICON,
            color=color if ready else ft.Colors.ON_SURFACE_VARIANT,
        ),
        width=_HERO_ICON + 54,
        height=_HERO_ICON + 54,
        border_radius=(_HERO_ICON + 54) // 2,
        bgcolor=ft.Colors.with_opacity(
            tokens.OPACITY_SUBTLE, color if ready else ft.Colors.ON_SURFACE_VARIANT
        ),
        alignment=ft.Alignment.CENTER,
    )


def _systems_panel(systems_ready: int, page) -> ft.Container:
    return AppStyles.glass_card(
        ft.Column(
            [
                ft.Text(
                    "TELEMETRY SYSTEMS",
                    size=tokens.FONT_XS,
                    weight=ft.FontWeight.W_700,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.ProgressBar(
                    value=min(1.0, systems_ready / len(_SYSTEMS)),
                    color=AppColors.PRIMARY,
                    bgcolor=ft.Colors.with_opacity(
                        tokens.OPACITY_SUBTLE, ft.Colors.ON_SURFACE
                    ),
                    bar_height=4,
                    width=240,
                ),
                ft.Text(
                    f"{systems_ready} of {len(_SYSTEMS)} systems live",
                    size=tokens.FONT_XS,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
            ],
            spacing=tokens.SPACE_XS,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        page=page,
        padding=tokens.SPACE_LG,
    )


def _build_brand_slide(page, systems_ready: int) -> ft.Column:
    return ft.Column(
        [
            build_logo(page, height=72),
            ft.Container(height=tokens.SPACE_LG),
            ft.Text(
                "Planetary\nCommand Center",
                size=tokens.FONT_XXL,
                weight=ft.FontWeight.W_800,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.ON_SURFACE,
                font_family="Outfit",
            ),
            ft.Container(height=tokens.SPACE_MD),
            ft.Text(
                "Live earthquakes, wildfires, floods, air quality and space "
                "weather — fused into one command view for any point on Earth.",
                size=tokens.FONT_MD,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
                font_family="Outfit",
            ),
            ft.Container(height=tokens.SPACE_LG),
            _systems_panel(systems_ready, page),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
    )


def _build_location_slide(
    page,
    search_query: str,
    search_results: list[dict],
    on_search_change,
    on_pick_city,
    on_locate_gps,
) -> ft.Column:
    """Locality slide — reuses the home search bar (inline suggestions + GPS
    trailing button with IP fallback) so the deck and dashboard behave alike."""
    return ft.Column(
        [
            _hero_icon(ft.Icons.EXPLORE_ROUNDED, AppColors.OCEAN),
            ft.Container(height=tokens.SPACE_LG),
            ft.Text(
                "Where should we\nstand watch?",
                size=tokens.FONT_XXL,
                weight=ft.FontWeight.W_800,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.ON_SURFACE,
                font_family="Outfit",
            ),
            ft.Container(height=tokens.SPACE_MD),
            ft.Text(
                "Pick a city — feeds localize in the background while you finish here.",
                size=tokens.FONT_MD,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
                font_family="Outfit",
            ),
            ft.Container(height=tokens.SPACE_LG),
            ft.Container(
                content=build_location_search_bar(
                    page,
                    search_query,
                    search_results,
                    on_search_change,
                    on_pick_city,
                    on_locate_gps,
                ),
                width=420,
                alignment=ft.Alignment.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
    )


def _build_ready_slide(page, systems_ready: int) -> ft.Column:
    ready = systems_ready >= len(_SYSTEMS)
    return ft.Column(
        [
            _hero_icon(
                (
                    ft.Icons.ROCKET_LAUNCH_ROUNDED
                    if ready
                    else ft.Icons.SATELLITE_ROUNDED
                ),
                AppColors.PRIMARY,
                ready=ready,
            ),
            ft.Container(height=tokens.SPACE_LG),
            ft.Text(
                "All Systems\nOperational" if ready else "Systems\nSyncing",
                size=tokens.FONT_XXL,
                weight=ft.FontWeight.W_800,
                text_align=ft.TextAlign.CENTER,
                color=ft.Colors.ON_SURFACE,
                font_family="Outfit",
            ),
            ft.Container(height=tokens.SPACE_MD),
            ft.Text(
                "Enter now — anything still syncing finishes as you explore.",
                size=tokens.FONT_MD,
                color=ft.Colors.ON_SURFACE_VARIANT,
                text_align=ft.TextAlign.CENTER,
                font_family="Outfit",
            ),
            ft.Container(height=tokens.SPACE_LG),
            AppStyles.glass_card(
                ft.Column(
                    [_sys_row(label, _is_live(f)) for label, f in _SYSTEMS],
                    spacing=tokens.SPACE_SM,
                ),
                page=page,
                padding=tokens.SPACE_LG,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=0,
    )


def build_onboarding_view(
    page: ft.Page | None,
    page_idx: int,
    systems_ready: int,
    search_query: str,
    search_results: list[dict],
    picked_name: str,
    on_next,
    on_skip,
    on_swipe,
    on_dot_click,
    on_search_change,
    on_pick_city,
    on_locate_gps,
) -> Control:
    """Builds the onboarding slide deck for the given slide index (testable)."""
    is_last = page_idx == 2

    if page_idx == 0:
        middle = _build_brand_slide(page, systems_ready)
    elif page_idx == 1:
        middle = _build_location_slide(
            page,
            search_query,
            search_results,
            on_search_change,
            on_pick_city,
            on_locate_gps,
        )
    else:
        middle = _build_ready_slide(page, systems_ready)

    # Dot indicators (tappable, active dot stretches into a pill)
    dots = [
        ft.GestureDetector(
            content=ft.Container(
                width=24 if i == page_idx else 8,
                height=8,
                border_radius=4,
                bgcolor=AppColors.PRIMARY
                if i == page_idx
                else ft.Colors.with_opacity(
                    tokens.OPACITY_MEDIUM, ft.Colors.ON_SURFACE
                ),
                animate=ft.Animation(tokens.ANIM_SLOW, "easeOut"),
            ),
            on_tap=lambda e, idx=i: on_dot_click(idx),
        )
        for i in range(3)
    ]

    cta_label = "Enter Planetary Command" if is_last else "Next"

    return ft.Container(
        expand=True,
        gradient=ft.LinearGradient(
            begin=ft.Alignment.TOP_CENTER,
            end=ft.Alignment.BOTTOM_CENTER,
            colors=[
                ft.Colors.SURFACE,
                ft.Colors.with_opacity(0.06, AppColors.PRIMARY),
            ],
        ),
        content=ft.Column(
            expand=True,
            spacing=0,
            controls=[
                # Top bar — Skip button (hidden on last slide)
                ft.Container(
                    padding=ft.Padding(
                        tokens.SPACE_LG, tokens.SPACE_MD, tokens.SPACE_LG, 0
                    ),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.END,
                        controls=[
                            ft.TextButton(
                                "Skip",
                                visible=not is_last,
                                on_click=on_skip,
                                style=ft.ButtonStyle(
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ),
                        ],
                    ),
                ),
                # Middle — swipeable slide content fills all remaining space
                ft.Container(
                    expand=True,
                    alignment=ft.Alignment.CENTER,
                    content=ft.GestureDetector(
                        content=ft.Container(
                            content=middle,
                            alignment=ft.Alignment.CENTER,
                            padding=ft.Padding(tokens.SPACE_XL, 0, tokens.SPACE_XL, 0),
                        ),
                        on_horizontal_drag_end=on_swipe,
                    ),
                ),
                # Bottom — dots + CTA + disclaimer pinned to bottom
                ft.Container(
                    padding=ft.Padding(
                        tokens.SPACE_LG, 0, tokens.SPACE_LG, tokens.SPACE_LG
                    ),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=tokens.SPACE_MD,
                        controls=[
                            ft.Row(
                                controls=dots,
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=tokens.SPACE_SM,
                            ),
                            ft.FilledButton(
                                content=ft.Text(
                                    cta_label,
                                    size=tokens.FONT_MD,
                                    weight=ft.FontWeight.W_600,
                                    font_family="Outfit",
                                    color=ft.Colors.WHITE,
                                ),
                                icon=ft.Icons.ROCKET_LAUNCH_ROUNDED
                                if is_last
                                else ft.Icons.ARROW_FORWARD_ROUNDED,
                                on_click=on_next,
                                width=340,
                                height=52,
                                style=ft.ButtonStyle(
                                    bgcolor=AppColors.PRIMARY,
                                    shape=ft.RoundedRectangleBorder(
                                        radius=tokens.RADIUS_XL
                                    ),
                                ),
                            ),
                            ft.Text(
                                "Live telemetry from USGS, NASA, NOAA, Copernicus & "
                                "Open-Meteo. No account required."
                                if picked_name == ""
                                else f"Standing watch over {picked_name}. Live "
                                "telemetry from USGS, NASA, NOAA, Copernicus & "
                                "Open-Meteo.",
                                size=tokens.FONT_XXS,
                                color=ft.Colors.with_opacity(
                                    tokens.OPACITY_DIM, ft.Colors.ON_SURFACE
                                ),
                                text_align=ft.TextAlign.CENTER,
                                max_lines=2,
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )


@ft.component
def OnboardingScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)
    page_idx, set_page_idx = ft.use_state(0)

    search_query, set_search_query = ft.use_state("")
    search_results, set_search_results = ft.use_state([])
    picked_name, set_picked_name = ft.use_state("")
    _is_searching, set_is_searching = ft.use_state(False)
    debounced_q = use_debounce(search_query, 350)

    from flet import context as flet_context

    page = flet_context.page

    # Live readiness — re-renders as background telemetry lands
    systems_ready = _systems_ready()

    is_last = page_idx == 2

    async def _do_search(q: str) -> None:
        if len(q.strip()) >= 2:
            set_is_searching(True)
            try:
                results = await GeocodingService.search_cities(q)
                set_search_results(results)
            except Exception as ex:
                logger.warning("Onboarding city search failed: %s", ex)
                set_search_results([])
            finally:
                set_is_searching(False)
        else:
            set_search_results([])

    async def _on_pick_city(r: dict) -> None:
        """Pre-localize feeds in the background — select_coordinates ends with
        refresh_all, so the localized refetch streams while the deck finishes."""
        set_search_query("")
        set_search_results([])
        set_picked_name(r["name"])
        if controller.select_coordinates:
            await controller.select_coordinates(
                r["latitude"],
                r["longitude"],
                r["name"],
                r.get("country", ""),
                silent=True,
            )

    async def _on_locate_gps(self=None, *args):
        """GPS/IP locate from onboarding — native geolocator with IP fallback."""
        if controller.locate_user:
            await controller.locate_user()
            set_picked_name(app_state.current_location_name)

    async def _finish():
        state.has_accepted_terms = True
        state.is_first_launch = False
        state.telemetry_version += 1
        if controller.dismiss_onboarding:
            controller.dismiss_onboarding()
        if controller.save_setting:
            await controller.save_setting(STORAGE_ONBOARDING_DONE, "true")

    def _tap_haptic():
        with contextlib.suppress(Exception):
            asyncio.create_task(ft.HapticFeedback().light_impact())

    def _on_next(e=None):
        _tap_haptic()
        if is_last:
            asyncio.create_task(_finish())
        else:
            set_page_idx(page_idx + 1)

    def _on_skip(e):
        _tap_haptic()
        asyncio.create_task(_finish())

    def _on_swipe(e: ft.DragEndEvent):
        if e.primary_velocity is not None:
            if e.primary_velocity < -200 and not is_last:
                _tap_haptic()
                set_page_idx(page_idx + 1)
            elif e.primary_velocity > 200 and page_idx > 0:
                _tap_haptic()
                set_page_idx(page_idx - 1)

    def _on_dot_click(idx: int):
        _tap_haptic()
        set_page_idx(idx)

    def _on_search_change(e):
        q = e.control.value or ""
        set_search_query(q)

    ft.use_effect(
        lambda: asyncio.create_task(_do_search(debounced_q)),
        [debounced_q],
    )

    return build_onboarding_view(
        page,
        page_idx,
        systems_ready,
        search_query,
        search_results,
        picked_name,
        _on_next,
        _on_skip,
        _on_swipe,
        _on_dot_click,
        _on_search_change,
        _on_pick_city,
        _on_locate_gps,
    )


__all__ = ["OnboardingScreen", "build_onboarding_view"]
