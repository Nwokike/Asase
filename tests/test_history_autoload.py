"""Dossier history auto-load regression (D2 Batch 3)."""


def test_radius_history_auto_load_wired():
    from pathlib import Path

    src = Path("src/screens/report_screen.py").read_text()
    # Auto effect on mount + location change; manual island gone.
    assert "_auto_radius_history" in src
    assert "state.current_lat, state.current_lon" in src
    assert "Tap Load to fetch" not in src
