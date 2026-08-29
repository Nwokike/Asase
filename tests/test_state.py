"""Tests for AppState."""

from core.state import AppState


def test_app_state_defaults():
    s = AppState()
    assert s.is_online is True
    assert s.min_magnitude_filter == 2.5
    assert s.temp_unit == "celsius"
    assert len(s.earthquakes) == 0
    assert len(s.disasters) == 0
