"""Staleness chips + empty states + history auto-count (D2 Batch 3)."""

import flet as ft
from flet_tree import walk_texts

from components.empty_state import EmptyState
from components.telemetry_card import _MiniSpark


def test_mini_spark_renders_bars():
    spark = _MiniSpark([1.0, 2.0, 3.0], "#10B981")
    assert isinstance(spark, ft.Row)
    assert len(spark.controls) == 3


def test_mini_spark_skips_garbage():
    spark = _MiniSpark([1.0, "--", None, 2.0], "#10B981")
    assert isinstance(spark, ft.Row)
    assert len(spark.controls) == 2


def test_mini_spark_empty_returns_container():
    assert isinstance(_MiniSpark([], "#10B981"), ft.Container)
    assert isinstance(_MiniSpark(None, "#10B981"), ft.Container)


def test_telemetry_card_accepts_glance_props():
    import inspect

    from components.telemetry_card import TelemetryCard

    params = inspect.signature(TelemetryCard).parameters
    assert "event_time" in params
    assert "spark_values" in params


def test_empty_state_has_action():
    from flet_tree import walk_buttons

    es = EmptyState(
        icon=ft.Icons.SEARCH_OFF_ROUNDED,
        title="No results",
        subtitle="Try another spelling.",
        action_text="Clear search",
        on_action=lambda: None,
    )
    buttons = list(walk_buttons(es))
    assert len(buttons) == 1
    texts = [t.value for t in walk_texts(es)]
    assert "No results" in texts


def test_staleness_chip_text_format():
    from core.state import state
    from core.units import feed_age

    state.feed_updated = {}
    assert feed_age("usgs") == "—"
