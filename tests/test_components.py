"""Comprehensive tests for Asase UI components."""

import flet as ft
from flet_tree import walk, walk_buttons, walk_icons, walk_texts

from components.banner_ad import build_banner_ad
from components.hazard_map import (
    HazardMap,
    build_event_detail_sheet,
    build_hazard_marker,
)
from components.home.focus_banner import build_focus_banner
from components.map.map_scan_section import build_map_scan_section
from components.report.ai_briefing_section import build_ai_briefing_section
from components.section_header import SectionHeader
from components.sparkline_chart import TelemetryLineChart
from components.telemetry_card import TelemetryCard, build_severity_badge
from core.theme import AppColors


def test_section_header():
    sh = SectionHeader("Planetary Defense")
    assert isinstance(sh, ft.Container)
    texts = list(walk_texts(sh))
    assert len(texts) == 1
    assert texts[0].value == "PLANETARY DEFENSE"

    # With action
    sh_action = SectionHeader("Radar", action_text="Expand", on_action=lambda _: None)
    assert isinstance(sh_action, ft.Container)
    texts_act = [t.value for t in walk_texts(sh_action)]
    assert "RADAR" in texts_act
    assert "EXPAND" in texts_act


def test_severity_badge():
    for sev in ["low", "moderate", "high", "critical", "unknown"]:
        badge = build_severity_badge(sev, sev)
        assert isinstance(badge, ft.Container)
        texts = list(walk_texts(badge))
        assert len(texts) == 1
        assert texts[0].value == sev.upper()


def test_telemetry_card():
    card = TelemetryCard(
        icon=ft.Icons.AIR_ROUNDED,
        title="Air Quality",
        value="42",
        subtitle="PM2.5: 8.5 µg/m³",
        severity="low",
        accent_color=AppColors.PRIMARY,
    )
    assert isinstance(card, ft.Container)
    texts = [t.value for t in walk_texts(card)]
    assert "42" in texts
    assert "Air Quality" in texts
    assert "PM2.5: 8.5 µg/m³" in texts

    icons = list(walk_icons(card))
    assert len(icons) >= 1


def test_telemetry_card_clickable():
    # Whole-card on_click flows through to the glass card container
    clicked = []
    card = TelemetryCard(
        icon=ft.Icons.WAVES_ROUNDED,
        title="M 4.2 - 12km S of Volcano",
        value="",
        subtitle="Depth 10.0km",
        severity="moderate",
        on_click=lambda e: clicked.append(e),
    )
    assert isinstance(card, ft.Container)
    assert card.on_click is not None
    assert card.ink is True  # ripple feedback for clickable cards


def test_focus_banner_states():
    # Collapsed: compact pill with the location name
    pill = build_focus_banner(
        page=None,
        location_name="Enugu",
        country="Nigeria",
        elevation_m=118,
        temperature=29,
        us_aqi=42,
        kp_index=2.0,
        nearest_hazard_text=None,
        nearest_hazard_color=AppColors.WARNING,
        expanded=False,
        is_loading=False,
        on_toggle=lambda: None,
        on_open_dossier=lambda: None,
    )
    texts = [t.value for t in walk_texts(pill)]
    assert any("Tracking: Enugu" in t for t in texts)
    assert not any("OPEN FULL DOSSIER" in t for t in texts)

    # Expanded: summary card with stat chips + dossier button + hazard chip
    expanded = build_focus_banner(
        page=None,
        location_name="Enugu",
        country="Nigeria",
        elevation_m=118,
        temperature=29,
        us_aqi=42,
        kp_index=2.0,
        nearest_hazard_text="M4.2 quake • 210 km away",
        nearest_hazard_color=AppColors.WARNING,
        expanded=True,
        is_loading=False,
        on_toggle=lambda: None,
        on_open_dossier=lambda: None,
    )
    texts_e = [t.value for t in walk_texts(expanded)]
    assert any("Enugu, Nigeria" in t for t in texts_e)
    assert any("118 m" in t for t in texts_e)
    assert any("29°C" in t for t in texts_e)
    assert any("AQI 42" in t for t in texts_e)
    assert any("Kp 2.0" in t for t in texts_e)
    assert any("210 km away" in t for t in texts_e)
    assert any("OPEN FULL DOSSIER" in t for t in texts_e)

    # Missing telemetry degrades to n/a instead of crashing
    degraded = build_focus_banner(
        page=None,
        location_name="Nowhere",
        country="",
        elevation_m=0,
        temperature=None,
        us_aqi="",
        kp_index="",
        nearest_hazard_text=None,
        nearest_hazard_color=AppColors.WARNING,
        expanded=True,
        is_loading=True,
        on_toggle=lambda: None,
        on_open_dossier=lambda: None,
    )
    texts_d = [t.value for t in walk_texts(degraded)]
    assert any(t == "n/a" for t in texts_d)
    assert any("Updating live telemetry" in t for t in texts_d)


def test_sparkline_chart_rendering():
    # Valid values
    chart = TelemetryLineChart(values=[10.0, 20.0, 15.0, 35.0, 30.0])
    assert isinstance(chart, ft.Container)

    # Empty / Insufficient values fallback
    chart_empty = TelemetryLineChart(values=[])
    assert isinstance(chart_empty, ft.Container)
    texts = list(walk_texts(chart_empty))
    assert len(texts) == 1
    assert "Awaiting" in texts[0].value or "Insufficient" in texts[0].value


def test_telemetry_line_chart_multi_series_and_step():
    # 2-series chart (actual + mean) with discrete step direction and axis labels
    chart_multi = TelemetryLineChart(
        values=[10.0, 25.0, 40.0],
        secondary_values=[12.0, 20.0, 30.0],
        step_direction=0.0,
        curved=False,
        bottom_labels=["+1d", "+2d", "+3d"],
        left_axis_title="m³/s",
    )
    assert isinstance(chart_multi, ft.Container)
    import flet_charts as fc

    lc = chart_multi.content
    assert isinstance(lc, fc.LineChart)
    assert len(lc.data_series) == 2
    assert lc.data_series[1].dash_pattern == [6, 4]  # secondary series is dashed
    assert lc.bottom_axis is not None
    assert lc.left_axis is not None


def test_hazard_map_component():
    eqs = [
        {
            "id": "eq1",
            "title": "M5.0 Tokyo",
            "latitude": 35.6,
            "longitude": 139.7,
            "magnitude": 5.0,
            "type": "earthquake",
        }
    ]
    disasters = [
        {
            "id": "dis1",
            "title": "Fire Alert",
            "latitude": -33.8,
            "longitude": 151.2,
            "type": "wildfire",
        }
    ]
    hmap = HazardMap(
        lat=0.0,
        lon=0.0,
        zoom=2.0,
        earthquakes=eqs,
        disasters=disasters,
    )
    assert isinstance(hmap, ft.Container)


def test_build_hazard_marker():
    eq_marker = build_hazard_marker(
        {"latitude": 10.0, "longitude": 20.0, "magnitude": 6.5, "type": "earthquake"}
    )
    assert eq_marker is not None
    assert eq_marker.coordinates.latitude == 10.0
    assert eq_marker.coordinates.longitude == 20.0

    fire_marker = build_hazard_marker(
        {"latitude": -10.0, "longitude": -20.0, "type": "wildfire"}
    )
    assert fire_marker is not None

    flood_marker = build_hazard_marker(
        {"latitude": 5.0, "longitude": 15.0, "type": "flood"}
    )
    assert flood_marker is not None


def test_build_event_detail_sheet():
    event = {
        "type": "earthquake",
        "title": "M 5.2 - 42km NE of Hachijo-jima, Japan",
        "latitude": 33.4,
        "longitude": 140.2,
        "magnitude": 5.2,
        "depth_km": 35.7,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/xyz",
    }
    sheet = build_event_detail_sheet(
        event, on_close=lambda: None, on_open_url=lambda u: None
    )
    assert isinstance(sheet, ft.Container)
    texts = [t.value for t in walk_texts(sheet)]
    assert any("EARTHQUAKE" in t for t in texts)
    assert any("Hachijo-jima" in t for t in texts)
    assert any("Magnitude M5.2" in t for t in texts)
    assert any("Depth 35.7 km" in t for t in texts)

    # TextButton/FilledButton render labels as `content` — Text objects (read
    # .value) or plain strings, depending on construction — not walked Texts.
    from flet_tree import walk

    def _label(b):
        c = b.content
        return c.value if isinstance(c, ft.Text) else str(c)

    buttons = [c for c in walk(sheet) if isinstance(c, ft.TextButton)]
    assert any("SOURCE" in _label(b) for b in buttons)

    # With dossier/share handlers, the sheet offers the full deep-dive path
    full_sheet = build_event_detail_sheet(
        event,
        on_close=lambda: None,
        on_open_url=lambda u: None,
        on_view_dossier=lambda: None,
        on_share=lambda m: None,
    )
    full_walk = list(walk(full_sheet))
    filled = [c for c in full_walk if isinstance(c, ft.FilledButton)]
    assert any("VIEW FULL DOSSIER" in _label(b) for b in filled)
    full_buttons = [c for c in full_walk if isinstance(c, ft.TextButton)]
    assert any("SHARE" in _label(b) for b in full_buttons)

    # No URL → no source button
    bare = build_event_detail_sheet(
        {"type": "flood", "title": "Flood Alert", "latitude": 1.0, "longitude": 2.0},
        on_close=lambda: None,
        on_open_url=lambda u: None,
    )
    buttons_bare = [c for c in walk(bare) if isinstance(c, ft.TextButton)]
    assert not any("SOURCE" in _label(b) for b in buttons_bare)


def test_banner_ad():
    ad = build_banner_ad(None)
    assert isinstance(ad, ft.Container)


def test_ai_sections_render_markdown():
    # Briefing answers render as rich Markdown, not raw asterisk soup
    briefing = build_ai_briefing_section(
        "**Primary Concern:** Rising river discharge.",
        False,
        False,
        "",
        lambda e: None,
        lambda e: None,
        lambda e: None,
        model="qwen/qwen3.8-27b",
    )
    md = [c for c in walk(briefing) if isinstance(c, ft.Markdown)]
    assert len(md) == 1
    assert md[0].value == "**Primary Concern:** Rising river discharge."
    assert md[0].selectable is True
    assert md[0].extension_set == ft.MarkdownExtensionSet.GITHUB_WEB

    # Map scan panel — same rich rendering
    scan = build_map_scan_section(
        "**Cluster:** Dense seismic group SE of marker.",
        False,
        False,
        "",
        "google/diffusiongemma-26b-a4b-it",
        lambda e: None,
        lambda e: None,
        lambda e: None,
    )
    md_scan = [c for c in walk(scan) if isinstance(c, ft.Markdown)]
    assert len(md_scan) == 1
    assert md_scan[0].value.startswith("**Cluster:**")


def test_markdown_stylesheet_theme():
    from core.theme import AppStyles

    sheet_dark = AppStyles.markdown_stylesheet(is_dark=True)
    sheet_light = AppStyles.markdown_stylesheet(is_dark=False)
    assert isinstance(sheet_dark, ft.MarkdownStyleSheet)
    assert sheet_dark.p_text_style is not None
    assert sheet_dark.code_text_style is not None
    assert sheet_light.code_text_style.bgcolor != sheet_dark.code_text_style.bgcolor


def test_space_g_scale_and_forecast_helpers():
    from screens.space_screen import (
        build_g_scale_meter,
        build_kp_forecast_chips,
        g_level_from_kp,
        kp_severity_color,
    )

    assert g_level_from_kp(1.67) == 0
    assert g_level_from_kp(5.2) == 1
    assert g_level_from_kp(6.0) == 2
    assert g_level_from_kp(7.4) == 3
    assert g_level_from_kp(8.2) == 4
    assert g_level_from_kp(9.0) == 5
    assert kp_severity_color(3.0) == AppColors.SEVERITY_LOW
    assert kp_severity_color(5.0) == AppColors.SEVERITY_MODERATE
    assert kp_severity_color(7.0) == AppColors.SEVERITY_CRITICAL

    meter = build_g_scale_meter(2)
    texts = [t.value for t in walk_texts(meter)]
    assert texts == ["G0", "G1", "G2", "G3", "G4", "G5"]

    chips = build_kp_forecast_chips(
        [
            {"time_tag": "2026-09-01T00:00:00", "kp": 3.0},
            {"time_tag": "2026-09-01T03:00:00", "kp": 6.5},
        ]
    )
    chip_texts = [t.value for t in walk_texts(chips)]
    assert "00:00" in chip_texts
    assert "Kp 3.0" in chip_texts
    assert "Kp 6.5" in chip_texts
    assert build_kp_forecast_chips([]) is None


def test_app_header():
    from components.app_header import build_app_header

    # Every screen uses the same consistent branding: reactive icon + title text.
    # page=None resolves to dark mode, so the icon is tinted white.
    hdr = build_app_header(
        page=None,
        title="Asase",
        subtitle="EARTH INTELLIGENCE",
        on_refresh=lambda: None,
        on_settings=lambda: None,
    )
    assert isinstance(hdr, ft.Container)
    images = [c for c in walk(hdr) if isinstance(c, ft.Image)]
    assert any(img.src == "/icon.svg" for img in images)
    icon_img = next(img for img in images if img.src == "/icon.svg")
    assert icon_img.color == ft.Colors.WHITE  # dark-mode white tint
    texts = [t.value for t in walk_texts(hdr)]
    assert "Asase" in texts
    assert "EARTH INTELLIGENCE" in texts


def test_about_card_and_onboarding_use_reactive_logo():
    from components.settings.sections_about import build_about_card
    from screens.onboarding_screen import _SLIDES, build_onboarding_view

    # page=None resolves to dark mode → white-wordmark logo variant.
    about = build_about_card(page=None)
    about_images = [c for c in walk(about) if isinstance(c, ft.Image)]
    assert any(img.src == "/logo_dark.svg" for img in about_images)
    about_texts = [t.value for t in walk_texts(about)]
    assert "Asase" not in about_texts  # wordmark is inside the logo asset

    # Family-standard slide deck (Sherlock pattern): the brand slide shows the
    # theme-reactive wordmark, feature slides render one capability each, and
    # the wordmark never appears as plain text anywhere in the deck.
    def _noop(*_args):
        pass

    deck_texts = []
    for idx in range(len(_SLIDES)):
        view = build_onboarding_view(None, idx, _noop, _noop, _noop, _noop)
        deck_texts += [t.value for t in walk_texts(view)]
        # String button labels (e.g. TextButton("Skip")) live on .content
        deck_texts += [
            b.content
            for b in walk_buttons(view)
            if isinstance(getattr(b, "content", None), str)
        ]
        if idx == 0:
            slide_images = [c for c in walk(view) if isinstance(c, ft.Image)]
            assert any(img.src == "/logo_dark.svg" for img in slide_images)
    assert "Asase" not in deck_texts  # wordmark is inside the logo asset
    assert "Enter Planetary Command" in deck_texts  # final-slide CTA
    assert "Skip" in deck_texts  # top-right skip on non-final slides
    assert "Next" in deck_texts  # non-final CTA label
    assert "Planetary\nCommand Center" in deck_texts  # brand-slide title


def test_location_search_bar():
    from components.home.location_search_bar import build_location_search_bar

    results = [
        {
            "name": "Tokyo",
            "country": "Japan",
            "latitude": 35.68,
            "longitude": 139.69,
            "elevation": 40,
        }
    ]
    bar = build_location_search_bar(
        page=None,
        search_query="Tok",
        search_results=results,
        on_search_change=lambda _: None,
        on_select_city=lambda _: None,
        on_locate_gps=lambda: None,
    )
    assert isinstance(bar, ft.Container)
    assert isinstance(bar.content, ft.Column)
    # Full-screen SearchBar (DDGS/Sherlock pattern — no hidden overlay)
    search = bar.content.controls[0]
    assert isinstance(search, ft.SearchBar)
    assert search.full_screen is True
    assert search.value == "Tok"
    # Suggestions render as visible ListTiles below the bar, not in the overlay
    assert len(bar.content.controls) == 2
    panel = bar.content.controls[1]
    assert isinstance(panel, ft.Container)
    assert isinstance(panel.content, ft.Column)
    tiles = [c for c in panel.content.controls if isinstance(c, ft.ListTile)]
    assert len(tiles) == 1

    # Empty results → just the bar, no suggestion panel
    empty_bar = build_location_search_bar(
        page=None,
        search_query="",
        search_results=[],
        on_search_change=lambda _: None,
        on_select_city=lambda _: None,
        on_locate_gps=lambda: None,
    )
    assert isinstance(empty_bar.content, ft.Column)
    assert len(empty_bar.content.controls) == 1
