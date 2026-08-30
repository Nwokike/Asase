"""Comprehensive tests for Asase UI components."""

import flet as ft
from flet_tree import walk_icons, walk_texts

from components.banner_ad import build_banner_ad
from components.hazard_map import (
    HazardMap,
    build_event_detail_sheet,
    build_hazard_marker,
)
from components.section_header import SectionHeader
from components.sparkline_chart import TelemetryLineChart
from components.telemetry_card import TelemetryCard, build_severity_badge
from core.theme import AppColors


def test_section_header():
    sh = SectionHeader("Planetary Defense")
    assert isinstance(sh, ft.Container)
    texts = list(walk_texts(sh))
    assert len(texts) == 1
    assert texts[0].value == "PLANETARY DEFENSE"

    # With action
    sh_action = SectionHeader("Radar", action_text="Expand", on_action=lambda _: None)
    assert isinstance(sh_action, ft.Container)
    texts_act = [t.value for t in walk_texts(sh_action)]
    assert "RADAR" in texts_act
    assert "EXPAND" in texts_act


def test_severity_badge():
    for sev in ["low", "moderate", "high", "critical", "unknown"]:
        badge = build_severity_badge(sev, sev)
        assert isinstance(badge, ft.Container)
        texts = list(walk_texts(badge))
        assert len(texts) == 1
        assert texts[0].value == sev.upper()


def test_telemetry_card():
    card = TelemetryCard(
        icon=ft.Icons.AIR_ROUNDED,
        title="Air Quality",
        value="42",
        subtitle="PM2.5: 8.5 µg/m³",
        severity="low",
        accent_color=AppColors.PRIMARY,
    )
    assert isinstance(card, ft.Container)
    texts = [t.value for t in walk_texts(card)]
    assert "42" in texts
    assert "Air Quality" in texts
    assert "PM2.5: 8.5 µg/m³" in texts

    icons = list(walk_icons(card))
    assert len(icons) >= 1


def test_sparkline_chart_rendering():
    # Valid values
    chart = TelemetryLineChart(values=[10.0, 20.0, 15.0, 35.0, 30.0])
    assert isinstance(chart, ft.Container)

    # Empty / Insufficient values fallback
    chart_empty = TelemetryLineChart(values=[])
    assert isinstance(chart_empty, ft.Container)
    texts = list(walk_texts(chart_empty))
    assert len(texts) == 1
    assert "Awaiting" in texts[0].value or "Insufficient" in texts[0].value


def test_hazard_map_component():
    eqs = [
        {
            "id": "eq1",
            "title": "M5.0 Tokyo",
            "latitude": 35.6,
            "longitude": 139.7,
            "magnitude": 5.0,
            "type": "earthquake",
        }
    ]
    disasters = [
        {
            "id": "dis1",
            "title": "Fire Alert",
            "latitude": -33.8,
            "longitude": 151.2,
            "type": "wildfire",
        }
    ]
    hmap = HazardMap(
        lat=0.0,
        lon=0.0,
        zoom=2.0,
        earthquakes=eqs,
        disasters=disasters,
    )
    assert isinstance(hmap, ft.Container)


def test_build_hazard_marker():
    eq_marker = build_hazard_marker(
        {"latitude": 10.0, "longitude": 20.0, "magnitude": 6.5, "type": "earthquake"}
    )
    assert eq_marker is not None
    assert eq_marker.coordinates.latitude == 10.0
    assert eq_marker.coordinates.longitude == 20.0

    fire_marker = build_hazard_marker(
        {"latitude": -10.0, "longitude": -20.0, "type": "wildfire"}
    )
    assert fire_marker is not None

    flood_marker = build_hazard_marker(
        {"latitude": 5.0, "longitude": 15.0, "type": "flood"}
    )
    assert flood_marker is not None


def test_build_event_detail_sheet():
    event = {
        "type": "earthquake",
        "title": "M 5.2 - 42km NE of Hachijo-jima, Japan",
        "latitude": 33.4,
        "longitude": 140.2,
        "magnitude": 5.2,
        "depth_km": 35.7,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/xyz",
    }
    sheet = build_event_detail_sheet(
        event, on_close=lambda: None, on_open_url=lambda u: None
    )
    assert isinstance(sheet, ft.Container)
    texts = [t.value for t in walk_texts(sheet)]
    assert any("EARTHQUAKE" in t for t in texts)
    assert any("Hachijo-jima" in t for t in texts)
    assert any("Magnitude M5.2" in t for t in texts)
    assert any("Depth 35.7 km" in t for t in texts)

    # TextButton renders its `content` label outside walked Text children
    from flet_tree import walk

    buttons = [c for c in walk(sheet) if isinstance(c, ft.TextButton)]
    assert any("OPEN SOURCE DATA" in str(b.content) for b in buttons)

    # No URL → no source button
    bare = build_event_detail_sheet(
        {"type": "flood", "title": "Flood Alert", "latitude": 1.0, "longitude": 2.0},
        on_close=lambda: None,
        on_open_url=lambda u: None,
    )
    buttons_bare = [c for c in walk(bare) if isinstance(c, ft.TextButton)]
    assert not any("OPEN SOURCE DATA" in str(b.content) for b in buttons_bare)


def test_banner_ad():
    ad = build_banner_ad(None)
    assert isinstance(ad, ft.Container)


def test_app_header():
    from components.app_header import build_app_header

    hdr = build_app_header(
        page=None,
        title="Asase",
        subtitle="EARTH INTELLIGENCE",
        on_refresh=lambda: None,
        on_settings=lambda: None,
    )
    assert isinstance(hdr, ft.Container)
    texts = [t.value for t in walk_texts(hdr)]
    assert "Asase" in texts
    assert "EARTH INTELLIGENCE" in texts


def test_location_search_bar():
    from components.home.location_search_bar import build_location_search_bar

    results = [
        {
            "name": "Tokyo",
            "country": "Japan",
            "latitude": 35.68,
            "longitude": 139.69,
            "elevation": 40,
        }
    ]
    bar = build_location_search_bar(
        page=None,
        search_query="Tok",
        search_results=results,
        on_search_change=lambda _: None,
        on_select_city=lambda _: None,
        on_locate_gps=lambda: None,
    )
    assert isinstance(bar, ft.Container)
    assert isinstance(bar.content, ft.Column)
    # Full-screen SearchBar (DDGS/Sherlock pattern — no hidden overlay)
    search = bar.content.controls[0]
    assert isinstance(search, ft.SearchBar)
    assert search.full_screen is True
    assert search.value == "Tok"
    # Suggestions render as visible ListTiles below the bar, not in the overlay
    assert len(bar.content.controls) == 2
    panel = bar.content.controls[1]
    assert isinstance(panel, ft.Container)
    assert isinstance(panel.content, ft.Column)
    tiles = [c for c in panel.content.controls if isinstance(c, ft.ListTile)]
    assert len(tiles) == 1

    # Empty results → just the bar, no suggestion panel
    empty_bar = build_location_search_bar(
        page=None,
        search_query="",
        search_results=[],
        on_search_change=lambda _: None,
        on_select_city=lambda _: None,
        on_locate_gps=lambda: None,
    )
    assert isinstance(empty_bar.content, ft.Column)
    assert len(empty_bar.content.controls) == 1
