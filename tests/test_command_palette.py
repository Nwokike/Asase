"""Command palette filter regressions (M7).

TextField.on_change can deliver ``None`` before the first keystroke —
filter_palette must treat it as an empty query, not crash on .strip().
"""

from components.command_palette import filter_palette

_INDEX = [
    {"type": "action", "label": "Open Full Map", "sub": "Navigation", "callback": None},
    {"type": "action", "label": "Refresh Feeds", "sub": "Data", "callback": None},
    {
        "type": "event",
        "label": "M4.2 near Enugu",
        "sub": "Earthquake • 2m ago",
        "callback": None,
    },
]


def test_none_query_returns_full_index():
    assert filter_palette(_INDEX, None) == _INDEX


def test_empty_and_blank_queries_return_full_index():
    assert filter_palette(_INDEX, "") == _INDEX
    assert filter_palette(_INDEX, "   ") == _INDEX


def test_query_filters_case_insensitively():
    results = filter_palette(_INDEX, "MAP")
    assert len(results) == 1
    assert results[0]["label"] == "Open Full Map"


def test_query_matches_label_or_sub():
    assert [r["label"] for r in filter_palette(_INDEX, "navigation")] == [
        "Open Full Map"
    ]
    assert [r["label"] for r in filter_palette(_INDEX, "earthquake")] == [
        "M4.2 near Enugu"
    ]


def test_no_match_returns_empty():
    assert filter_palette(_INDEX, "zzz") == []
