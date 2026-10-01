"""Unit-preference end-to-end regressions (Batch J)."""

import pytest

from core.state import state


@pytest.fixture(autouse=True)
def _restore_units():
    orig_temp, orig_speed = state.temp_unit, state.speed_unit
    yield
    state.temp_unit, state.speed_unit = orig_temp, orig_speed


def test_format_temp_celsius_default():
    from core.units import format_temp

    state.temp_unit = "celsius"
    assert format_temp(25.4) == "25°C"
    assert format_temp("--") == "n/a"
    assert format_temp(None) == "n/a"


def test_format_temp_fahrenheit():
    from core.units import format_temp

    state.temp_unit = "fahrenheit"
    assert format_temp(0) == "32°F"
    assert format_temp(100) == "212°F"


def test_format_speed_kmh_default():
    from core.units import format_speed

    state.speed_unit = "kmh"
    assert format_speed(50) == "50 km/h"
    assert format_speed("--") == "n/a"


def test_format_speed_mph():
    from core.units import format_speed

    state.speed_unit = "mph"
    assert format_speed(100) == "62 mph"


def test_focus_banner_honors_temp_pref():
    from flet_tree import walk_texts

    from components.home.focus_banner import build_focus_banner

    state.temp_unit = "fahrenheit"
    banner = build_focus_banner(
        page=None,
        location_name="Lagos",
        country="Nigeria",
        elevation_m=10.0,
        temperature=25.0,
        us_aqi=42,
        kp_index=2.0,
        nearest_hazard_text=None,
        nearest_hazard_color="#fff",
        expanded=True,
        is_loading=False,
        on_toggle=lambda: None,
        on_open_dossier=lambda: None,
    )
    texts = [t.value for t in walk_texts(banner)]
    assert any("77°F" in (t or "") for t in texts)
    assert not any("25°C" in (t or "") for t in texts)


def test_weather_section_honors_prefs():
    from flet_tree import walk_texts

    from components.report.weather_indicators_section import (
        build_weather_indicators_section,
    )

    state.temp_unit = "fahrenheit"
    state.speed_unit = "mph"
    section = build_weather_indicators_section(
        temp=20.0,
        apparent_temp=22.0,
        wind_gust=50.0,
        wind_speed=30.0,
        cape=500.0,
        pressure=1013.0,
        humidity=60.0,
    )
    texts = [t.value for t in walk_texts(section)]
    joined = " ".join(t or "" for t in texts)
    assert "68°F" in joined
    assert "31 mph" in joined
    assert "°C" not in joined
    assert "km/h" not in joined
