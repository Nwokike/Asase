"""Flare class parsing."""

from services.space_weather_service import _parse_flare_class


def test_parse_x_class():
    msg, cls = _parse_flare_class([{"classType": "X2.1"}])
    assert cls == "X2.1" and "X" in msg


def test_parse_m_class():
    _, cls = _parse_flare_class([{"classType": "M1.0"}])
    assert cls.startswith("M")


def test_parse_flux_fallback_x():
    _, cls = _parse_flare_class([{"flux": "2e-04"}])
    assert cls == "X"


def test_parse_flux_fallback_m():
    _, cls = _parse_flare_class([{"flux": "2e-05"}])
    assert cls == "M"


def test_parse_flux_fallback_c():
    _, cls = _parse_flare_class([{"flux": "2e-06"}])
    assert cls == "C"


def test_empty():
    msg, cls = _parse_flare_class([])
    assert cls == "" and "Active" in msg


def test_best_rank():
    _, cls = _parse_flare_class(
        [{"classType": "C1.0"}, {"classType": "M5.0"}, {"classType": "X1.0"}]
    )
    assert cls.startswith("X")
