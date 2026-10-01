"""Report-screen numeric hardening.

Regression tests: feed sentinels ("--", None) must not crash risk math;
storm formula follows the CAPE-band model; AQI trend takes the freshest
(most recent) 12 readings.
"""

from screens.report_screen import safe_float, storm_risk_from_cape_gust


def test_safe_float_guards_sentinels():
    assert safe_float("--") is None
    assert safe_float(None) is None
    assert safe_float("") is None
    assert safe_float("garbage") is None
    assert safe_float(42) == 42.0
    assert safe_float("3.5") == 3.5
    assert safe_float(None, 0.0) == 0.0


def test_storm_risk_follows_cape_bands():
    # Below 300 CAPE: low base; extreme CAPE dominates.
    assert storm_risk_from_cape_gust(0, 0) < 25.0
    assert storm_risk_from_cape_gust(1500, 0) >= 60.0
    assert storm_risk_from_cape_gust(3000, 0) >= 85.0
    # Severe gusts register even with modest CAPE.
    assert storm_risk_from_cape_gust(100, 80) >= 40.0
    # Sentinels never crash and never inflate.
    assert storm_risk_from_cape_gust("--", "--") == storm_risk_from_cape_gust(0, 0)
    assert storm_risk_from_cape_gust(None, None) == storm_risk_from_cape_gust(0, 0)


def test_storm_risk_capped_at_100():
    assert storm_risk_from_cape_gust(5000, 200) == 100.0


def test_aqi_trend_takes_most_recent_12():
    """Oldest-first hourly arrays: the tail is the fresh window."""
    hourly = list(range(1, 25))  # 1..24
    trend = [parsed for v in hourly[-12:] if (parsed := safe_float(v)) is not None]
    assert trend == [float(v) for v in range(13, 25)]


def test_aqi_trend_skips_non_numeric():
    hourly = [10, "--", None, 20, "bad", 30]
    trend = [parsed for v in hourly[-12:] if (parsed := safe_float(v)) is not None]
    assert trend == [10.0, 20.0, 30.0]
