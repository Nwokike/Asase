"""Tests for AppState observable reactivity — the root fix of the 2026-08 repair.

Verifies that AppState is an Observable, that field writes notify listeners,
that lists/dicts are auto-wrapped into ObservableList/ObservableDict, and that
the singleton `state` is observable too (what use_context subscribes to).
"""

import flet as ft
from flet.components.observable import ObservableDict, ObservableList

from core.state import AppState, state


def _listener(events: list):
    def fn(sender, field):
        events.append((sender, field))

    return fn


def test_app_state_is_observable():
    s = AppState()
    assert isinstance(s, ft.Observable)


def test_field_write_notifies():
    s = AppState()
    events: list = []
    dispose = s.subscribe(_listener(events))
    try:
        s.selected_hazard_type = "wildfire"
        assert events == [(s, "selected_hazard_type")]
    finally:
        dispose()


def test_write_same_value_does_not_notify():
    s = AppState()
    events: list = []
    dispose = s.subscribe(_listener(events))
    try:
        s.selected_hazard_type = "all"  # same as default
        assert events == []
    finally:
        dispose()


def test_lists_are_observable_wrapped():
    s = AppState()
    assert isinstance(s.earthquakes, ObservableList)
    assert isinstance(s.bookmarks, ObservableList)
    assert isinstance(s.recent_searches, ObservableList)
    assert isinstance(s.disasters, ObservableList)


def test_dicts_are_observable_wrapped():
    s = AppState()
    assert isinstance(s.weather_data, ObservableDict)
    assert isinstance(s.space_weather, ObservableDict)
    assert isinstance(s.air_quality_data, ObservableDict)


def test_list_append_notifies():
    s = AppState()
    events: list = []
    dispose = s.subscribe(_listener(events))
    try:
        s.bookmarks.append({"name": "Lagos"})
        assert events == [(s, "bookmarks")]
        assert s.bookmarks == [{"name": "Lagos"}]
    finally:
        dispose()


def test_whole_list_reassignment_notifies():
    s = AppState()
    events: list = []
    dispose = s.subscribe(_listener(events))
    try:
        s.earthquakes = [{"place": "Tokyo"}]
        assert events == [(s, "earthquakes")]
        assert isinstance(s.earthquakes, ObservableList)
    finally:
        dispose()


def test_dict_setitem_notifies():
    s = AppState()
    events: list = []
    dispose = s.subscribe(_listener(events))
    try:
        s.space_weather["kp_index"] = 4.5
        assert events == [(s, "space_weather")]
    finally:
        dispose()


def test_singleton_state_is_observable():
    assert isinstance(state, ft.Observable)
    assert isinstance(state, AppState)


def test_dataclass_semantics_preserved():
    # The stacked decorator must not break dataclass construction/defaults.
    s = AppState()
    assert s.is_online is True
    assert s.min_magnitude_filter == 2.5
    assert s.temp_unit == "celsius"
    assert s.speed_unit == "kmh"
    assert s.selected_hazard_type == "all"
    assert s.earthquakes == []
    assert s.bookmarks == []

    # Dataclass equality between two fresh instances still holds.
    assert AppState() == AppState()


def test_notify_version_increments():
    s = AppState()
    before = s.__version__
    s.selected_hazard_type = "flood"
    assert s.__version__ == before + 1
