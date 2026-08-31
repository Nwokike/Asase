"""Asase AI Intelligence — grounded telemetry narration via the Kiri Gateway.

Same integration pattern as akili-app and MarkItDown: hardcoded family app key,
SSE streaming, fail-soft. The AI never invents data — every prompt is grounded
in real telemetry already fetched into AppState (text briefings) or in a
screenshot of the app's own live hazard map (map scans).
"""

from __future__ import annotations

import base64
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass

import httpx

from core.constants import GATEWAY_APP_SECRET, GATEWAY_CHAT_URL
from core.state import state

logger = logging.getLogger("asase.ai")

# Gateway JSON body cap is 10MB; leave headroom for the prompt around it.
_MAX_IMAGE_B64_CHARS = 9_000_000

# Defense-in-depth (spaninsight pattern): some fallback models inline their
# thinking in content even with parsed reasoning. Never display reasoning.
_THINK_RE = re.compile(
    r"<(?:think|thought|reasoning)>.*?(?:</(?:think|thought|reasoning)>|$)",
    re.DOTALL | re.IGNORECASE,
)

SYSTEM_PROMPT = (
    "You are Asase, a planetary earth-intelligence analyst. You are given REAL "
    "measured telemetry for one location (seismic, air quality, weather, "
    "hydrology, marine, geomagnetic). Turn those numbers into a brief, "
    "plain-language risk briefing a normal person can act on. Rules: use ONLY "
    "the provided measurements — never invent or estimate values you were not "
    "given; if a value is missing, say it is unavailable; be specific and "
    "reference the actual numbers; no hedging filler; calm factual tone like a "
    "flight safety card. Format as clean Markdown: a single bold lead line with "
    "the most important concern, then at most 4 short bullet points."
)

DEFAULT_QUESTION = (
    "Give me the current risk briefing for this location: the most important "
    "hazard or concern right now, air quality guidance, and whether any "
    "weather or geomagnetic conditions need attention."
)

MAP_SCAN_SYSTEM_PROMPT = (
    "You are Asase's hazard-map analyst. You are given a screenshot of the "
    "app's live hazard map plus the tracked location's measured telemetry. "
    "Describe ONLY what is actually visible in the image — hazard markers, "
    "their colors, density and spatial pattern around the tracked location — "
    "and connect visible patterns to the provided measurements. Never invent "
    "events, places, or numbers that are not visible in the image or present "
    "in the measurements. Lead with a single bold line naming the most "
    "significant visible hazard cluster, then at most 4 short Markdown bullet "
    "points. Plain language a normal person can act on."
)

DEFAULT_SCAN_QUESTION = (
    "Scan this map: what hazards are visible around my tracked location, and "
    "is anything clustered nearby I should know about?"
)

_USER_AGENT = "Asase-Earth-Intelligence/1.0"


@dataclass
class AIResult:
    """One streamed gateway answer: assembled text + the model that produced it."""

    text: str = ""
    model: str = ""


def build_dossier_context() -> str:
    """Serialize the current location's real telemetry into a grounded context."""
    w = (state.weather_data or {}).get("current", {})
    aq = (state.air_quality_data or {}).get("current", {})
    fd = (state.flood_data or {}).get("daily", {})
    marine = (state.marine_data or {}).get("current", {})
    sw = state.space_weather or {}
    discharge = fd.get("river_discharge") or []
    flare = (
        f", latest flare class {sw.get('flare_class')}" if sw.get("flare_class") else ""
    )

    lines = [
        f"Location: {state.current_location_name} ({state.current_country or 'unknown country'})",
        f"Coordinates: {state.current_lat:.4f} lat, {state.current_lon:.4f} lon, elevation {state.current_elevation:.0f} m",
        f"Earthquakes tracked (24h, M{state.min_magnitude_filter}+): {len(state.earthquakes)} events",
        f"Active natural events (NASA EONET): {len(state.disasters)}",
        f"Temperature: {w.get('temperature_2m', 'n/a')} C (feels like {w.get('apparent_temperature', 'n/a')})",
        f"Humidity: {w.get('relative_humidity_2m', 'n/a')} %, surface pressure: {w.get('surface_pressure', 'n/a')} hPa",
        f"Wind: {w.get('wind_speed_10m', 'n/a')} km/h, gusts {w.get('wind_gusts_10m', 'n/a')} km/h",
        f"CAPE convective index: {w.get('cape', 'n/a')} J/kg, precipitation: {w.get('precipitation', 'n/a')} mm",
        f"US AQI: {aq.get('us_aqi', 'n/a')} (PM2.5 {aq.get('pm2_5', 'n/a')}, PM10 {aq.get('pm10', 'n/a')} ug/m3)",
        f"Ozone {aq.get('ozone', 'n/a')}, NO2 {aq.get('nitrogen_dioxide', 'n/a')}, dust {aq.get('dust', 'n/a')} ug/m3",
        f"River discharge 7-day (m3/s): {discharge[:7] if discharge else 'n/a'}",
        f"Wave height: {marine.get('wave_height', 'n/a')} m, swell {marine.get('swell_wave_height', 'n/a')} m",
        f"Geomagnetic Kp: {sw.get('kp_index', 'n/a')} ({sw.get('geomagnetic_status', 'n/a')})",
        f"Solar activity: {sw.get('solar_activity', 'n/a')}{flare}",
    ]
    return "\n".join(str(line) for line in lines)


def _parse_sse_obj(line: str) -> dict | None:
    """Parse one SSE `data:` line into its JSON object, else None."""
    if not line or not line.startswith("data:"):
        return None
    data = line[5:].strip()
    if not data or data == "[DONE]":
        return None
    try:
        obj = json.loads(data)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) else None


def _content_delta(obj: dict) -> str | None:
    """Read only the content field of a chunk — never reasoning fields."""
    choices = obj.get("choices") or []
    if not choices:
        return None
    choice = choices[0] or {}
    delta = (choice.get("delta") or {}).get("content")
    if not delta:
        delta = (choice.get("message") or {}).get("content")
    if not delta:
        return None
    return _THINK_RE.sub("", delta)


def extract_stream_delta(line: str) -> str | None:
    """Extract the content delta from one SSE `data:` line, else None.

    Reasoning is never returned: only `content`/`message.content` fields are
    read (never `reasoning`/`reasoning_content`), and any inline thinking
    tags are stripped defensively.
    """
    obj = _parse_sse_obj(line)
    return _content_delta(obj) if obj else None


async def _stream_chat(payload: dict, on_token: Callable[[str], None]) -> AIResult:
    """POST one payload to the gateway and stream the answer back.

    Fail-soft: any transport or server error returns an empty AIResult — the
    caller shows an offline-friendly message, telemetry is unaffected.
    """
    headers = {
        "Authorization": f"Bearer {GATEWAY_APP_SECRET}",
        "User-Agent": _USER_AGENT,
    }

    collected: list[str] = []
    model = ""
    try:
        async with (
            httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client,
            client.stream(
                "POST", GATEWAY_CHAT_URL, json=payload, headers=headers
            ) as response,
        ):
            if response.status_code != 200:
                logger.warning("Gateway chat non-200: %s", response.status_code)
                return AIResult()
            async for line in response.aiter_lines():
                obj = _parse_sse_obj(line)
                if not obj:
                    continue
                if not model and obj.get("model"):
                    model = str(obj["model"])
                delta = _content_delta(obj)
                if delta:
                    collected.append(delta)
                    try:
                        on_token(delta)
                    except Exception:
                        pass
    except Exception as ex:
        logger.warning("AI streaming failed (fail-soft): %s", ex)
        return AIResult()
    return AIResult(_THINK_RE.sub("", "".join(collected)).strip(), model)


async def stream_briefing(
    question: str,
    on_token: Callable[[str], None],
    context: str | None = None,
) -> AIResult:
    """Stream a grounded answer about the location's telemetry, per text route."""
    payload = {
        "task_type": "text",
        "stream": True,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"MEASURED TELEMETRY:\n{context or build_dossier_context()}\n\n"
                    f"QUESTION: {question}"
                ),
            },
        ],
    }
    return await _stream_chat(payload, on_token)


async def stream_map_scan(
    png_bytes: bytes,
    question: str,
    on_token: Callable[[str], None],
    context: str | None = None,
) -> AIResult:
    """Stream an analysis of a hazard-map screenshot, via the multimodal route.

    Follow-up questions on the same capture re-send the identical image with
    the new question. Oversized captures fail soft (gateway caps JSON bodies
    at 10MB) — capture at pixel_ratio=1 to stay comfortably under it.
    """
    try:
        b64 = base64.b64encode(png_bytes).decode("ascii")
    except Exception as ex:
        logger.warning("Map capture not encodable (fail-soft): %s", ex)
        return AIResult()
    if len(b64) > _MAX_IMAGE_B64_CHARS:
        logger.warning(
            "Map capture too large for gateway: %.1fMB base64", len(b64) / 1_000_000
        )
        return AIResult()

    payload = {
        "task_type": "multimodal",
        "stream": True,
        "messages": [
            {"role": "system", "content": MAP_SCAN_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "The screenshot shows the app's hazard map. "
                            f"MEASURED TELEMETRY:\n"
                            f"{context or build_dossier_context()}\n\n"
                            f"QUESTION: {question}"
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64}"},
                    },
                ],
            },
        ],
    }
    return await _stream_chat(payload, on_token)
