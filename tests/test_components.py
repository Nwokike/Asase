"""Comprehensive tests for Asase UI components."""

import flet as ft
from flet_tree import walk_icons, walk_texts

from components.banner_ad import build_banner_ad
from components.hazard_map import HazardMap, build_hazard_marker
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
    chart_empty = TelemetryLineChart(values=[10.0])
    assert isinstance(chart_empty, ft.Container)
    texts = list(walk_texts(chart_empty))
    assert len(texts) == 1
    assert "Insufficient" in texts[0].value


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


def test_banner_ad():
    ad = build_banner_ad(None)
    assert isinstance(ad, ft.Container)
