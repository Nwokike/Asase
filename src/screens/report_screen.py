"""ReportScreen — Deep-dive Location Risk Dossier, Multi-Hazard Analysis & Radar Assessment."""

from __future__ import annotations

import asyncio
import logging
import time

import flet as ft
from flet import Control

from components.app_header import build_app_header
from components.banner_ad import build_banner_ad
from components.report.ai_briefing_section import build_ai_briefing_section
from components.report.air_quality_section import build_air_quality_section
from components.report.hydrology_marine_section import (
    build_hydrology_section,
    build_marine_section,
)
from components.report.threat_radar_section import build_threat_radar_section
from components.report.weather_indicators_section import (
    build_weather_indicators_section,
)
from components.section_header import SectionHeader
from core import tokens
from core.notify import show_snack
from core.theme import AppColors, AppStyles, is_dark_mode
from services.ai_service import DEFAULT_QUESTION, stream_briefing
from state.app_state import AppStateCtx
from state.controller_ctx import ControllerMethodsCtx

logger = logging.getLogger("asase.report")


@ft.component
def ReportScreen() -> Control:
    state = ft.use_context(AppStateCtx)
    controller = ft.use_context(ControllerMethodsCtx)

    from flet import context as flet_context

    page = flet_context.page

    # Extract AQI & Pollutants
    aqi_data = state.air_quality_data.get("current", {})
    us_aqi = aqi_data.get("us_aqi", 0)
    pm25 = aqi_data.get("pm2_5", 0)
    pm10 = aqi_data.get("pm10", 0)
    co = aqi_data.get("carbon_monoxide", 0)
    no2 = aqi_data.get("nitrogen_dioxide", 0)
    o3 = aqi_data.get("ozone", 0)
    so2 = aqi_data.get("sulphur_dioxide", 0)
    dust = aqi_data.get("dust", 0)

    # Hourly AQI trend
    hourly_aqi = state.air_quality_data.get("hourly", {}).get("us_aqi", [])
    aqi_trend = [float(v) for v in hourly_aqi[:12] if v is not None]

    # Extract Hydrology & Marine
    flood_daily = state.flood_data.get("daily", {})
    river_discharge = flood_daily.get("river_discharge", [])
    discharge_trend = [float(v) for v in river_discharge[:7] if v is not None]
    max_discharge = max(discharge_trend) if discharge_trend else None

    marine_current = state.marine_data.get("current", {})
    wave_height = marine_current.get("wave_height")
    wave_period = marine_current.get("wave_period")
    swell_height = marine_current.get("swell_wave_height")

    # Extract Weather & Storm Indicators
    weather_data = state.weather_data.get("current", {})
    temp = weather_data.get("temperature_2m", "--")
    apparent_temp = weather_data.get("apparent_temperature", "--")
    humidity = weather_data.get("relative_humidity_2m", "--")
    pressure = weather_data.get("surface_pressure", "--")
    wind_speed = weather_data.get("wind_speed_10m", "--")
    wind_gust = weather_data.get("wind_gusts_10m", "--")
    cape = weather_data.get("cape", 0)

    # Space Weather
    kp_val = state.space_weather.get("kp_index", 0.0)

    # Overall Threat Dimensions (0 - 100 for Radar Chart)
    seismic_risk_val = min(100.0, len(state.earthquakes) * 2.5)
    storm_risk_val = min(
        100.0, (float(cape or 0) / 30.0) + (float(wind_gust or 0) * 0.8)
    )
    flood_risk_val = min(100.0, float(max_discharge) * 0.15) if max_discharge else 10.0
    pollution_risk_val = min(100.0, float(us_aqi or 0) * 0.5)
    geomagnetic_risk_val = min(100.0, float(kp_val) * 11.0)

    # Overall Safety Score Computation (0 - 100)
    risk_deductions = 0
    if us_aqi and us_aqi > 50:
        risk_deductions += min(30, (us_aqi - 50) * 0.3)
    if wind_gust and isinstance(wind_gust, (int, float)) and wind_gust > 40:
        risk_deductions += min(20, (wind_gust - 40) * 0.5)
    if cape and cape > 1000:
        risk_deductions += min(20, (cape - 1000) * 0.01)
    if max_discharge and max_discharge > 500:
        risk_deductions += min(20, (max_discharge - 500) * 0.02)

    safety_score = max(10, int(100 - risk_deductions))
    score_color = (
        AppColors.SEVERITY_LOW
        if safety_score >= 80
        else (
            AppColors.SEVERITY_MODERATE
            if safety_score >= 60
            else AppColors.SEVERITY_CRITICAL
        )
    )

    is_bookmarked = any(
        b.get("name") == state.current_location_name for b in state.bookmarks
    )

    def _toggle_bookmark_click(e):
        if controller.toggle_bookmark:
            loc = {
                "name": state.current_location_name,
                "latitude": state.current_lat,
                "longitude": state.current_lon,
                "country": state.current_country,
            }
            asyncio.create_task(controller.toggle_bookmark(loc))

    async def _export_dossier():
        summary_text = (
            f"🌍 ASASE PLANETARY DOSSIER: {state.current_location_name}\n"
            f"Coordinates: {state.current_lat:.4f}° N, {state.current_lon:.4f}° E\n"
            f"Safety Score: {safety_score}/100\n\n"
            f"• AQI: {us_aqi} (PM2.5: {pm25} µg/m³)\n"
            f"• Surface Temp: {temp}°C (Gusts: {wind_gust} km/h)\n"
            f"• CAPE Storm Index: {cape} J/kg\n"
            f"• Hydrology River Discharge: {max_discharge or 0:.1f} m³/s\n"
            f"• Geomagnetic Kp: {kp_val}\n"
            f"• Active Seismic Nearby: {len(state.earthquakes)} events\n\n"
            f"Generated via Asase Earth Intelligence"
        )
        if controller.share_text:
            await controller.share_text(
                summary_text, f"Planetary Risk Dossier - {state.current_location_name}"
            )
        else:
            try:
                if hasattr(page, "set_clipboard"):
                    await page.set_clipboard(summary_text)
                elif hasattr(page, "clipboard"):
                    await page.clipboard.set(summary_text)
                if page:
                    show_snack(
                        page, "Dossier copied to clipboard!", bgcolor=AppColors.SUCCESS
                    )
            except Exception as ex:
                logger.warning("Export dossier failed: %s", ex)
                if page:
                    show_snack(page, "Failed to copy dossier.", bgcolor=AppColors.ERROR)

    header_view = build_app_header(
        page,
        title="Dossier",
        subtitle="MULTI-HAZARD RISK ASSESSMENT",
        on_refresh=controller.refresh_all,
        on_settings=lambda: (
            controller.navigate_tab(4) if controller.navigate_tab else None
        ),
        save_setting_fn=controller.save_setting,
    )

    threat_radar = build_threat_radar_section(
        seismic_risk_val,
        storm_risk_val,
        flood_risk_val,
        pollution_risk_val,
        geomagnetic_risk_val,
    )
    radius_events, set_radius_events = ft.use_state(None)
    radius_loading, set_radius_loading = ft.use_state(False)

    # AI briefing state — tokens stream in, pumped to the UI in small batches
    ai_answer, set_ai_answer = ft.use_state("")
    ai_busy, set_ai_busy = ft.use_state(False)
    ai_unavailable, set_ai_unavailable = ft.use_state(False)
    ai_question, set_ai_question = ft.use_state("")
    ai_model, set_ai_model = ft.use_state("")
    # Supersede token: every fire bumps the generation; results from an
    # older fire (superseded by a newer location or question) no-op.
    ai_gen_ref = ft.use_ref(0)

    async def _run_ai(q: str):
        if not q.strip():
            return
        gen = (ai_gen_ref.current or 0) + 1
        ai_gen_ref.current = gen
        fired_at = (state.current_lat, state.current_lon)
        set_ai_busy(True)
        set_ai_answer("")
        set_ai_unavailable(False)
        set_ai_model("")

        buf: list[str] = []
        last_push = 0.0

        def _on_token(chunk: str):
            nonlocal last_push
            if ai_gen_ref.current != gen:
                return  # a newer request superseded this stream
            buf.append(chunk)
            now = time.monotonic()
            if now - last_push > 0.2:  # batch UI updates while streaming
                last_push = now
                set_ai_answer("".join(buf))

        try:
            result = await stream_briefing(q, _on_token)
            if ai_gen_ref.current != gen:
                return  # a newer briefing took over mid-stream
            set_ai_answer(result.text or "".join(buf))
            set_ai_model(result.model)
            if result.text:
                # Cache keyed to the exact coordinates it was generated for
                state.ai_briefing = {
                    "answer": result.text,
                    "model": result.model,
                    "lat": fired_at[0],
                    "lon": fired_at[1],
                }
            elif not (result.text or buf):
                set_ai_unavailable(True)
        except Exception as ex:
            logger.warning("AI briefing failed: %s", ex)
            if ai_gen_ref.current == gen:
                set_ai_unavailable(True)
        finally:
            if ai_gen_ref.current == gen:
                set_ai_busy(False)

    def _generate_briefing(e=None):
        if ai_busy:
            return
        asyncio.create_task(_run_ai(DEFAULT_QUESTION))

    def _ask_followup(e=None):
        q = ai_question
        set_ai_question("")
        if q.strip():
            asyncio.create_task(_run_ai(q))

    # The briefing is a function of the tracked LOCATION, not of screen
    # mounts: the effect fires on Dossier open and RE-FIRES for every
    # location change while it's open (search, card tap, map tap) — each
    # new dossier gets its own fresh briefing. A cache hit (the exact same
    # coordinates already briefed this session) hydrates instantly instead.
    # NOTE: use_effect invokes the setup with ZERO arguments.
    def _brief_for_location():
        cache = state.ai_briefing or {}
        if (
            cache.get("answer")
            and cache.get("lat") == state.current_lat
            and cache.get("lon") == state.current_lon
        ):
            set_ai_answer(str(cache["answer"]))
            set_ai_model(str(cache.get("model", "")))
            return
        asyncio.create_task(_run_ai(DEFAULT_QUESTION))

    ft.use_effect(_brief_for_location, [state.current_lat, state.current_lon])

    ai_section = build_ai_briefing_section(
        ai_answer,
        ai_busy,
        ai_unavailable,
        ai_question,
        _generate_briefing,
        _ask_followup,
        lambda e: set_ai_question(e.control.value or ""),
        ai_model,
        is_dark=is_dark_mode(page),
        on_open_link=(
            lambda url: (
                asyncio.create_task(controller.launch_url(url))
                if controller.launch_url
                else None
            )
        ),
    )

    async def _load_radius_history():
        if not controller.fetch_radius_history:
            return
        set_radius_loading(True)
        try:
            evs = await controller.fetch_radius_history(
                state.current_lat, state.current_lon, 500.0
            )
            set_radius_events(evs or [])
        except Exception as ex:
            logger.debug("Radius history load failed: %s", ex)
            set_radius_events([])
        finally:
            set_radius_loading(False)

    _radius_history_block = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(
                            ft.Icons.HISTORY_ROUNDED,
                            size=tokens.ICON_SM,
                            color=AppColors.PRIMARY,
                        ),
                        ft.Text(
                            "LOCAL SEISMIC HISTORY (500 KM)",
                            size=tokens.FONT_XS,
                            weight=ft.FontWeight.W_700,
                            color=AppColors.PRIMARY,
                        ),
                        ft.Container(expand=True),
                        ft.TextButton(
                            "Load",
                            on_click=lambda _: asyncio.create_task(
                                _load_radius_history()
                            ),
                        )
                        if radius_events is None
                        else ft.TextButton(
                            "Reload",
                            on_click=lambda _: asyncio.create_task(
                                _load_radius_history()
                            ),
                        ),
                    ],
                    spacing=tokens.SPACE_XS,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(
                    "Fetching…"
                    if radius_loading
                    else (
                        f"{len(radius_events)} events"
                        if radius_events is not None
                        else "Tap Load to fetch USGS FDSN 500 km history"
                    ),
                    size=tokens.FONT_XS,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                *(
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Text(
                                        f"M{float(e.get('magnitude', 0)):.1f}",
                                        size=tokens.FONT_XS,
                                        weight=ft.FontWeight.BOLD,
                                        color=AppColors.SEVERITY_HIGH,
                                    ),
                                    ft.Text(
                                        e.get("place", "")[:60],
                                        size=tokens.FONT_XS,
                                        color=ft.Colors.ON_SURFACE,
                                        expand=True,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                    ),
                                ],
                                spacing=tokens.SPACE_SM,
                            ),
                            padding=ft.Padding(
                                tokens.SPACE_SM,
                                tokens.SPACE_XS,
                                tokens.SPACE_SM,
                                tokens.SPACE_XS,
                            ),
                        )
                        for e in (radius_events or [])[:10]
                    ]
                ),
            ],
            spacing=tokens.SPACE_XS,
        ),
        padding=tokens.SPACE_MD,
    )
    hydrology_sec = build_hydrology_section(max_discharge, discharge_trend)
    marine_sec = build_marine_section(wave_height, swell_height, wave_period)
    air_quality_sec = build_air_quality_section(
        us_aqi, pm25, pm10, co, no2, o3, so2, dust, aqi_trend
    )
    weather_sec = build_weather_indicators_section(
        temp, apparent_temp, wind_gust, wind_speed, cape, pressure, humidity
    )

    return ft.ListView(
        controls=[
            header_view,
            ft.Container(height=tokens.SPACE_SM),
            # Location Hero Card
            ft.Container(
                content=AppStyles.glass_card(
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Row(
                                        [
                                            ft.Text(
                                                state.current_location_name,
                                                size=tokens.FONT_XL,
                                                weight=ft.FontWeight.BOLD,
                                                font_family="Outfit",
                                            ),
                                            ft.IconButton(
                                                icon=(
                                                    ft.Icons.STAR_ROUNDED
                                                    if is_bookmarked
                                                    else ft.Icons.STAR_BORDER_ROUNDED
                                                ),
                                                icon_color=(
                                                    AppColors.WARNING
                                                    if is_bookmarked
                                                    else ft.Colors.ON_SURFACE_VARIANT
                                                ),
                                                tooltip="Bookmark Location",
                                                on_click=_toggle_bookmark_click,
                                            ),
                                        ],
                                        spacing=tokens.SPACE_XS,
                                    ),
                                    ft.Text(
                                        f"Coordinates: {state.current_lat:.4f}° N, {state.current_lon:.4f}° E • Elevation: {int(state.current_elevation)}m",
                                        size=tokens.FONT_XS,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                        font_family="Outfit",
                                    ),
                                ],
                                spacing=tokens.SPACE_XXS,
                                expand=True,
                            ),
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            f"{safety_score}",
                                            size=tokens.FONT_XXL,
                                            weight=ft.FontWeight.BOLD,
                                            color=score_color,
                                            font_family="Outfit",
                                        ),
                                        ft.Text(
                                            "SAFETY SCORE",
                                            size=tokens.FONT_XXS,
                                            weight=ft.FontWeight.W_700,
                                            color=score_color,
                                        ),
                                    ],
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=0,
                                ),
                                padding=tokens.SPACE_SM,
                                border_radius=tokens.RADIUS_MD,
                                bgcolor=ft.Colors.with_opacity(0.12, score_color),
                                border=ft.Border.all(
                                    1, ft.Colors.with_opacity(0.3, score_color)
                                ),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    padding=tokens.SPACE_LG,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0
                ),
            ),
            # Actions
            ft.Container(
                content=ft.Row(
                    [
                        ft.FilledButton(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.Icons.SHARE_ROUNDED,
                                        size=tokens.ICON_SM,
                                        color=ft.Colors.WHITE,
                                    ),
                                    ft.Text(
                                        "Share Full Dossier",
                                        size=tokens.FONT_SM,
                                        weight=ft.FontWeight.W_600,
                                        color=ft.Colors.WHITE,
                                    ),
                                ],
                                spacing=4,
                            ),
                            style=ft.ButtonStyle(
                                bgcolor=AppColors.PRIMARY,
                                shape=ft.RoundedRectangleBorder(
                                    radius=tokens.RADIUS_MD
                                ),
                            ),
                            on_click=lambda _: asyncio.create_task(_export_dossier()),
                        ),
                        ft.OutlinedButton(
                            content=ft.Row(
                                [
                                    ft.Icon(ft.Icons.MAP_ROUNDED, size=tokens.ICON_SM),
                                    ft.Text("View on Map", size=tokens.FONT_SM),
                                ],
                                spacing=4,
                            ),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=tokens.RADIUS_MD)
                            ),
                            on_click=lambda _: (
                                controller.show_map() if controller.show_map else None
                            ),
                        ),
                    ],
                    spacing=tokens.SPACE_MD,
                ),
                padding=ft.Padding(
                    tokens.SPACE_LG, tokens.SPACE_SM, tokens.SPACE_LG, 0
                ),
            ),
            SectionHeader("PLANETARY THREAT RADAR PROFILE"),
            threat_radar,
            ai_section,
            _radius_history_block,
            SectionHeader("HYDROLOGY & GLOFAS RIVER DISCHARGE (7-DAY FORECAST)"),
            hydrology_sec,
            SectionHeader("MARINE DYNAMICS & COASTAL SWELL"),
            marine_sec,
            SectionHeader("AIR QUALITY & POLLUTANTS (OPEN-METEO AQI)"),
            air_quality_sec,
            SectionHeader("ATMOSPHERIC DYNAMICS & CONVECTIVE STORM INDEX"),
            weather_sec,
            ft.Container(height=tokens.SPACE_MD),
            build_banner_ad(page),
            ft.Container(height=tokens.SPACE_XXXL),
        ],
        spacing=0,
        expand=True,
    )
