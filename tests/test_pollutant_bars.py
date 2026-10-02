"""Pollutant BarChart regressions (Batch M)."""

import flet_charts as fc
from flet_tree import walk

from components.report.air_quality_section import (
    _safe_pollutant,
    build_air_quality_section,
    build_pollutant_bars,
)


def test_safe_pollutant_skips_missing():
    assert _safe_pollutant(12.5) == 12.5
    assert _safe_pollutant("--") is None
    assert _safe_pollutant(None) is None
    assert _safe_pollutant("") is None


def test_pollutant_bars_build_all_rods():
    chart = build_pollutant_bars(
        [
            ("PM2.5", 12.0, "#fff"),
            ("PM10", 20.0, "#fff"),
            ("CO", 300.0, "#fff"),
            ("NO₂", 15.0, "#fff"),
            ("O₃", 40.0, "#fff"),
            ("SO₂", 5.0, "#fff"),
            ("Dust", 8.0, "#fff"),
        ]
    )
    assert chart is not None
    bars = [c for c in walk(chart) if isinstance(c, fc.BarChart)]
    assert len(bars) == 1
    assert len(bars[0].groups) == 7
    assert bars[0].groups[2].rods[0].to_y == 300.0


def test_pollutant_bars_skip_missing_not_zero():
    chart = build_pollutant_bars(
        [("PM2.5", 12.0, "#fff"), ("CO", "--", "#fff"), ("NO₂", None, "#fff")]
    )
    assert chart is not None
    bars = [c for c in walk(chart) if isinstance(c, fc.BarChart)]
    assert len(bars[0].groups) == 1
    assert bars[0].groups[0].rods[0].to_y == 12.0


def test_pollutant_bars_all_missing_returns_none():
    assert build_pollutant_bars([("PM2.5", "--", "#fff")]) is None


def test_air_quality_section_embeds_comparison():
    section = build_air_quality_section(
        us_aqi=55,
        pm25=12.0,
        pm10=20.0,
        co=300.0,
        no2=15.0,
        o3=40.0,
        so2=5.0,
        dust=8.0,
        aqi_trend=[40.0, 45.0, 55.0],
    )
    bars = [c for c in walk(section) if isinstance(c, fc.BarChart)]
    assert len(bars) == 1
    assert len(bars[0].groups) == 7
