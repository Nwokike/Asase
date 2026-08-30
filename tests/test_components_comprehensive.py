"""Component smoke tests — mirrors KTV test_empty_state/test_loading_state."""

import flet as ft
from flet_tree import walk_texts

from components.empty_state import EmptyState
from components.offline_banner import build_offline_banner
from components.section_header import SectionHeader
from components.skeleton_loader import TelemetrySkeletonCard
from components.sparkline_chart import TelemetryLineChart


def test_empty_state_with_and_without_action():
    c1 = EmptyState(
        title="No data",
        subtitle="Try again",
        action_text="Retry",
        on_action=lambda: None,
    )
    texts = [t.value for t in walk_texts(c1)]
    assert "No data" in texts
    c2 = EmptyState(title="Empty")
    assert isinstance(c2, ft.Container)


def test_skeleton_card():
    c = TelemetrySkeletonCard(height=95)
    assert c is not None
    c2 = TelemetrySkeletonCard()
    assert c2 is not None


def test_offline_banner_visibility():
    b = build_offline_banner(True)
    assert b.visible is True
    b2 = build_offline_banner(False)
    assert b2.visible is False


def test_section_header():
    h = SectionHeader("TEST")
    assert isinstance(h, ft.Container)
    h2 = SectionHeader("TEST", action_text="Go", on_action=lambda _: None)
    assert isinstance(h2, ft.Container)


def test_line_chart_empty_and_filled():
    empty = TelemetryLineChart(values=[])
    assert isinstance(empty, ft.Container)
    filled = TelemetryLineChart(values=[1, 2, 3, 4])
    assert isinstance(filled, ft.Container)
