"""Comprehensive model coverage — severity, storm, AQI, noaa scale, eonet, geojson."""

import pytest

from models.atmospheric import CurrentAirQuality, CurrentWeather
from models.disasters import EonetCategory, EonetEvent, EonetGeometry
from models.seismic import EarthquakeFeature, EarthquakeProperties, GeoJsonPointGeometry
from models.space_weather import SpaceWeatherTelemetry


@pytest.mark.parametrize(
    "mag,alert,expected",
    [
        (7.5, "green", "critical"),
        (3.0, "red", "critical"),
        (3.0, "orange", "critical"),
        (5.0, "green", "high"),
        (3.0, "yellow", "high"),
        (3.5, "green", "moderate"),
        (3.0, "green", "moderate"),
        (2.9, "green", "low"),
        (1.0, None, "low"),
    ],
)
def test_severity_levels(mag, alert, expected):
    p = EarthquakeProperties(mag=mag, time=1700000000000, alert=alert)
    assert p.severity_level == expected


@pytest.mark.parametrize(
    "cape,expected",
    [
        (None, "low"),
        (0, "low"),
        (299, "low"),
        (300, "moderate"),
        (999, "moderate"),
        (1000, "high"),
        (2499, "high"),
        (2500, "extreme"),
        (3200, "extreme"),
    ],
)
def test_storm_risk_categories(cape, expected):
    assert CurrentWeather(cape=cape).storm_risk_category == expected


@pytest.mark.parametrize(
    "aqi,keyword",
    [
        (10, "Good"),
        (50, "Good"),
        (75, "Moderate"),
        (100, "Moderate"),
        (120, "Sensitive"),
        (150, "Sensitive"),
        (175, "Unhealthy"),
        (200, "Unhealthy"),
        (250, "Very Unhealthy"),
        (300, "Very Unhealthy"),
        (350, "Hazardous"),
        (None, "Good"),
        (0, "Good"),
    ],
)
def test_aqi_descriptors(aqi, keyword):
    assert keyword in CurrentAirQuality(us_aqi=aqi).aqi_health_descriptor


@pytest.mark.parametrize(
    "kp,expected",
    [
        (0, "G0"),
        (4.9, "G0"),
        (5.0, "G1"),
        (5.9, "G1"),
        (6.0, "G2"),
        (6.9, "G2"),
        (7.0, "G3"),
        (7.5, "G3"),
        (8.0, "G4"),
        (8.9, "G4"),
        (9.0, "G5"),
        (9.5, "G5"),
    ],
)
def test_noaa_scale(kp, expected):
    assert expected in SpaceWeatherTelemetry(kp_index=kp).noaa_scale


def test_geojson_point_edge():
    g = GeoJsonPointGeometry(coordinates=[10.0, 20.0])
    assert g.longitude == 10.0 and g.latitude == 20.0 and g.depth_km == 0.0
    g2 = GeoJsonPointGeometry(coordinates=[])
    assert g2.longitude == 0.0 and g2.latitude == 0.0


def test_eonet_hazard_types():
    def ev(cat_id, title=""):
        return EonetEvent(
            id="x",
            title="t",
            categories=[EonetCategory(id=cat_id, title=title or cat_id)],
            geometry=[],
        )

    assert ev("wildfires", "Wildfires").hazard_type == "wildfire"
    assert ev("severeStorms", "Storm").hazard_type == "storm"
    assert ev("volcanoes", "Volcano").hazard_type == "volcano"
    assert ev("floods", "Floods").hazard_type == "flood"
    assert ev("seaLakeIce").hazard_type == "disaster"
    assert ev("Cyclone", "Hurricane").hazard_type == "storm"


def test_eonet_geometry_point_and_polygon():
    assert EonetGeometry(coordinates=[]).point_coords == (0.0, 0.0)
    assert EonetGeometry(coordinates=[-120.0, 37.5]).point_coords == (-120.0, 37.5)
    assert EonetGeometry(coordinates=[[-120.0, 37.5]]).point_coords == (-120.0, 37.5)
    assert EonetGeometry(coordinates=[[[-120.0, 37.5]]]).point_coords == (-120.0, 37.5)


def test_earthquake_to_map_dict_fields():
    f = EarthquakeFeature(
        id="us1",
        properties=EarthquakeProperties(
            mag=5.5,
            place="Chile",
            time=1700000000000,
            title="M 5.5 Chile",
            url="http://x",
            tsunami=1,
            mmi=6.2,
        ),
        geometry=GeoJsonPointGeometry(coordinates=[-70.0, -33.0, 10.0]),
    )
    d = f.to_map_dict()
    assert (
        d["type"] == "earthquake"
        and d["tsunami"] is True
        and d["mmi"] == 6.2
        and d["depth_km"] == 10.0
        and d["severity"] in ("high", "critical")
    )


def test_formatted_time():
    p = EarthquakeProperties(mag=1.0, time=0, title="t")
    assert "1970" in p.formatted_time and "UTC" in p.formatted_time
