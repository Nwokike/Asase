"""Route wiring: tab indices resolve to the correct screens.

Regression test for the swapped Settings/History wiring
(show_settings rendered History and vice versa).
"""

from app_shell import _TAB_INDEX, resolve_dashboard_screen
from screens.history_screen import HistoryScreen
from screens.home_screen import HomeScreen
from screens.map_screen import MapScreen
from screens.settings_screen import SettingsScreen
from screens.space_screen import SpaceScreen


def test_tab_index_names_match_positions():
    assert _TAB_INDEX["History"] == 3
    assert _TAB_INDEX["Settings"] == 4


def test_resolve_dashboard_screen_routes_each_tab():
    assert resolve_dashboard_screen(0) is HomeScreen
    assert resolve_dashboard_screen(1) is MapScreen
    assert resolve_dashboard_screen(2) is SpaceScreen
    assert resolve_dashboard_screen(_TAB_INDEX["History"]) is HistoryScreen
    assert resolve_dashboard_screen(_TAB_INDEX["Settings"]) is SettingsScreen


def test_resolve_dashboard_screen_unknown_falls_through_to_settings():
    assert resolve_dashboard_screen(99) is SettingsScreen
