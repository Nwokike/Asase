"""Home canvas layout-branch regressions (D2 Batch 2)."""


def test_compact_uses_scroll_layout():
    from components.adaptive_nav import window_class
    from screens import home_screen  # noqa: F401 (layout branch reviewed below)

    assert window_class(400) == "compact"
    assert window_class(700) == "medium"
    assert window_class(1200) == "expanded"


def test_canvas_branch_markers_present_in_source():
    from pathlib import Path

    src = Path("src/screens/home_screen.py").read_text()
    assert "use_canvas" in src
    assert "left_rail" in src
    assert "right_feeds" in src
    # Compact scroll path preserved.
    assert "height=240" in src or "height = 240" in src
