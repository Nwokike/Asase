"""Tests for the AI risk briefing integration (Kiri Gateway /chat)."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import flet as ft
from flet_tree import walk, walk_texts

from components.report.ai_briefing_section import build_ai_briefing_section
from core.state import state
from services.ai_service import (
    DEFAULT_QUESTION,
    DEFAULT_SCAN_QUESTION,
    AIResult,
    build_dossier_context,
    extract_stream_delta,
    stream_briefing,
    stream_map_scan,
)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}"


def test_extract_stream_delta():
    assert (
        extract_stream_delta(
            _sse({"choices": [{"delta": {"content": "Air quality is"}}]})
        )
        == "Air quality is"
    )
    assert (
        extract_stream_delta(
            _sse({"choices": [{"message": {"content": "unsafe today."}}]})
        )
        == "unsafe today."
    )
    assert extract_stream_delta("data: [DONE]") is None
    assert extract_stream_delta("event: ping") is None
    assert extract_stream_delta("") is None
    assert extract_stream_delta("data: not-json") is None
    assert extract_stream_delta(_sse({"choices": []})) is None
    assert (
        extract_stream_delta(_sse({"choices": [{"delta": {"reasoning": "hmm"}}]}))
        is None
    )


def test_extract_stream_delta_strips_inline_thinking():
    line = _sse({"choices": [{"delta": {"content": "Air is fine."}}]})
    assert extract_stream_delta(line) == "Air is fine."
    # Unclosed thinking tag — strip to end (streaming defense)
    thinking = _sse(
        {"choices": [{"delta": {"content": "<think>hidden reasoning text"}}]}
    )
    assert "hidden reasoning" not in (extract_stream_delta(thinking) or "")
    assert extract_stream_delta(thinking) == ""
    # Closed thinking tag before real content
    closed = _sse(
        {
            "choices": [
                {"delta": {"content": "<reasoning>thoughts</reasoning>Kp is quiet."}}
            ]
        }
    )
    assert extract_stream_delta(closed) == "Kp is quiet."


class _FakeStreamContext:
    """Async context manager yielding SSE lines from a client.stream() call."""

    status_code = 200

    def __init__(self, lines):
        self._lines = lines

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def aiter_lines(self):
        async def _gen():
            for line in self._lines:
                yield line

        return _gen()


def _mock_httpx_client(client: MagicMock) -> MagicMock:
    """Make a MagicMock usable as `async with httpx.AsyncClient(...) as client`."""
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


async def test_stream_briefing_assembles_tokens():
    chunks = [
        _sse({"choices": [{"delta": {"content": "Kp is quiet. "}}]}),
        _sse({"choices": [{"delta": {"content": "AQI 42 is good."}}]}),
        "data: [DONE]",
    ]
    client = MagicMock()
    client.stream = MagicMock(return_value=_FakeStreamContext(chunks))
    with patch(
        "services.ai_service.httpx.AsyncClient",
        return_value=_mock_httpx_client(client),
    ):
        tokens: list[str] = []
        result = await stream_briefing("brief me", tokens.append)
    assert result.text == "Kp is quiet. AQI 42 is good."
    assert tokens == ["Kp is quiet. ", "AQI 42 is good."]


async def test_stream_briefing_reports_model_attribution():
    chunks = [
        _sse({"model": "qwen/qwen3.8-27b", "choices": [{"delta": {"content": "x"}}]}),
    ]
    client = MagicMock()
    client.stream = MagicMock(return_value=_FakeStreamContext(chunks))
    with patch(
        "services.ai_service.httpx.AsyncClient",
        return_value=_mock_httpx_client(client),
    ):
        result = await stream_briefing("brief me", lambda t: None)
    assert result.model == "qwen/qwen3.8-27b"


async def test_stream_briefing_non_200_returns_empty():
    client = MagicMock()
    ctx = _FakeStreamContext([])
    ctx.status_code = 503
    client.stream = MagicMock(return_value=ctx)
    with patch(
        "services.ai_service.httpx.AsyncClient",
        return_value=_mock_httpx_client(client),
    ):
        result = await stream_briefing("brief me", lambda t: None)
    assert result == AIResult()


async def test_stream_briefing_fails_soft():
    with patch(
        "services.ai_service.httpx.AsyncClient",
        side_effect=OSError("gateway unreachable"),
    ):
        result = await stream_briefing("brief me", lambda t: None)
    assert result.text == ""


async def test_stream_map_scan_sends_multimodal_image_payload():
    chunks = [_sse({"choices": [{"delta": {"content": "One cluster visible."}}]})]
    client = MagicMock()
    client.stream = MagicMock(return_value=_FakeStreamContext(chunks))
    with patch(
        "services.ai_service.httpx.AsyncClient",
        return_value=_mock_httpx_client(client),
    ) as _:
        result = await stream_map_scan(b"fakepng", "scan it", lambda t: None)
    assert result.text == "One cluster visible."
    # The payload posted to the gateway must be a multimodal image_url message
    payload = client.stream.call_args.kwargs["json"]
    assert payload["task_type"] == "multimodal"
    content = payload["messages"][-1]["content"]
    assert isinstance(content, list)
    image_part = next(p for p in content if p.get("type") == "image_url")
    assert image_part["image_url"]["url"].startswith("data:image/png;base64,")
    text_part = next(p for p in content if p.get("type") == "text")
    assert "scan it" in text_part["text"]


async def test_stream_map_scan_rejects_oversized_capture():
    # Fail soft without any HTTP call when the capture exceeds the body cap
    with patch("services.ai_service.httpx.AsyncClient") as ctor:
        result = await stream_map_scan(b"\x00" * 12_000_000, "scan", lambda t: None)
    assert result.text == ""
    ctor.assert_not_called()


def test_build_dossier_context_reflects_state():
    state.current_location_name = "Lagos"
    state.current_country = "Nigeria"
    state.current_lat = 6.5
    state.current_lon = 3.4
    state.weather_data = {"current": {"temperature_2m": 29, "wind_gusts_10m": 18}}
    state.air_quality_data = {"current": {"us_aqi": 55, "pm2_5": 12}}
    state.earthquakes = [{"id": 1}]
    try:
        ctx = build_dossier_context()
        assert "Lagos" in ctx
        assert "Nigeria" in ctx
        assert "1 events" in ctx
        assert "US AQI: 55" in ctx
        assert "Temperature: 29" in ctx
        assert "n/a" in ctx  # missing fields degrade explicitly
    finally:
        state.current_location_name = "Global Telemetry"
        state.current_country = ""
        state.current_lat = 6.5244
        state.current_lon = 3.3792
        state.weather_data = {}
        state.air_quality_data = {}
        state.earthquakes = []


def test_default_question_is_actionable():
    assert "risk briefing" in DEFAULT_QUESTION.lower()
    assert "hazards are visible" in DEFAULT_SCAN_QUESTION.lower()


def test_ai_briefing_section_initial_state():
    section = build_ai_briefing_section(
        answer="",
        busy=False,
        unavailable=False,
        question="",
        on_generate=lambda e: None,
        on_ask=lambda e: None,
        on_question_change=lambda e: None,
    )
    texts = [t.value for t in walk_texts(section)]
    assert any("Kiri Intelligence" in t for t in texts)
    assert any("Generate Briefing" in t for t in texts)
    # Idle, no answer → no streaming row, no unavailable note, no ask box
    assert not any("Analyzing live telemetry" in t for t in texts)
    assert not any("unavailable" in t for t in texts)
    assert not any(isinstance(c, ft.TextField) for c in walk(section))


def test_ai_briefing_section_busy_and_answer_states():
    busy_section = build_ai_briefing_section(
        "", True, False, "", lambda e: None, lambda e: None, lambda e: None
    )
    texts = [t.value for t in walk_texts(busy_section)]
    assert any("Analyzing live telemetry" in t for t in texts)

    answered = build_ai_briefing_section(
        "Kp is quiet; AQI 42 is good.",
        False,
        False,
        "",
        lambda e: None,
        lambda e: None,
        lambda e: None,
    )
    texts_a = [t.value for t in walk_texts(answered)]
    # The answer lives in a Markdown control, not plain Texts
    mds = [c for c in walk(answered) if isinstance(c, ft.Markdown)]
    assert len(mds) == 1 and "Kp is quiet" in mds[0].value
    assert any("Regenerate Briefing" in t for t in texts_a)
    assert any(isinstance(c, ft.TextField) for c in walk(answered))


def test_ai_briefing_section_unavailable_state():
    section = build_ai_briefing_section(
        "", False, True, "", lambda e: None, lambda e: None, lambda e: None
    )
    texts = [t.value for t in walk_texts(section)]
    assert any("unavailable right now" in t for t in texts)


def test_ai_briefing_section_shows_model_attribution():
    section = build_ai_briefing_section(
        "Kp is quiet.",
        False,
        False,
        "",
        lambda e: None,
        lambda e: None,
        lambda e: None,
        model="qwen/qwen3.8-27b",
    )
    texts = [t.value for t in walk_texts(section)]
    assert any("via qwen/qwen3.8-27b" in t for t in texts)

    # No attribution line when the model is unknown
    no_model = build_ai_briefing_section(
        "Kp is quiet.", False, False, "", lambda e: None, lambda e: None, lambda e: None
    )
    texts2 = [t.value for t in walk_texts(no_model)]
    assert not any(t and t.startswith("via ") for t in texts2)


def test_map_scan_section_states():
    from components.map.map_scan_section import build_map_scan_section

    idle = build_map_scan_section(
        "", False, False, "", "", lambda e: None, lambda e: None, lambda e: None
    )
    assert any("AI Scan This Map" in t for t in [x.value for x in walk_texts(idle)])

    answered = build_map_scan_section(
        "Dense quake cluster SE of the marker.",
        False,
        False,
        "",
        "google/diffusiongemma-26b-a4b-it",
        lambda e: None,
        lambda e: None,
        lambda e: None,
    )
    texts = [t.value for t in walk_texts(answered)]
    mds = [c for c in walk(answered) if isinstance(c, ft.Markdown)]
    assert len(mds) == 1 and "Dense quake cluster" in mds[0].value
    assert any("via google/diffusiongemma" in t for t in texts)

    busy = build_map_scan_section(
        "", True, False, "", "", lambda e: None, lambda e: None, lambda e: None
    )
    assert any("Scanning map view" in t for t in [x.value for x in walk_texts(busy)])
