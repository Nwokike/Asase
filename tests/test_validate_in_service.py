"""Validate-in-service regressions (Batch P)."""

from models.atmospheric import CurrentAirQuality, CurrentWeather
from services.atmospheric_service import _validate_section


def test_valid_payload_validates():
    out = _validate_section(
        CurrentWeather,
        {"temperature_2m": 29.5, "cape": 1500.0, "wind_gusts_10m": 20.0},
        "weather.current",
    )
    assert out["temperature_2m"] == 29.5
    assert out["cape"] == 1500.0
    # Computed fields ride along in the dump.
    assert out["storm_risk_category"] == "high"


def test_drift_passes_raw():
    raw = {"temperature_2m": "boiling", "cape": [1, 2, 3], "weird_new_key": 1}
    out = _validate_section(CurrentWeather, raw, "weather.current")
    assert out is raw


def test_empty_passes_through():
    assert _validate_section(CurrentAirQuality, {}, "aq") == {}
    assert _validate_section(CurrentAirQuality, None, "aq") is None


def test_aqi_descriptor_in_dump():
    out = _validate_section(CurrentAirQuality, {"us_aqi": 120}, "aq")
    assert out["aqi_health_descriptor"] == "Unhealthy for Sensitive Groups"
