"""Deep testing of Pydantic v2 data models."""

from models.atmospheric import CurrentAirQuality, CurrentWeather
from models.disasters import EonetCategory, EonetEvent, EonetGeometry
from models.geocoding import GeocodingLocation, GeocodingResponse
from models.seismic import (
    EarthquakeFeature,
    EarthquakeProperties,
    GeoJsonPointGeometry,
)
from models.space_weather import SpaceWeatherTelemetry


def test_seismic_model_validation():
    feature = EarthquakeFeature(
        id="us7000test",
        properties=EarthquakeProperties(
            mag=7.2,
            place="Fiji Region",
            time=1700000000000,
            alert="red",
            tsunami=1,
            title="M 7.2 - Fiji Region",
        ),
        geometry=GeoJsonPointGeometry(
            coordinates=[178.0, -18.0, 550.0],
        ),
    )
    assert feature.geometry.longitude == 178.0
    assert feature.geometry.latitude == -18.0
    assert feature.geometry.depth_km == 550.0
    assert feature.properties.has_tsunami_warning is True
    assert feature.properties.severity_level == "critical"

    d = feature.to_map_dict()
    assert d["id"] == "us7000test"
    assert d["severity"] == "critical"


def test_eonet_model_validation():
    event = EonetEvent(
        id="EONET_999",
        title="Active Wildfire",
        categories=[EonetCategory(id="wildfires", title="Wildfires")],
        geometry=[EonetGeometry(date="2026-08-29", coordinates=[-120.0, 37.5])],
    )
    assert event.hazard_type == "wildfire"
    assert event.primary_coordinates == (-120.0, 37.5)


def test_atmospheric_model_validation():
    weather = CurrentWeather(
        temperature_2m=32.0,
        cape=3200.0,
    )
    assert weather.storm_risk_category == "extreme"

    aqi = CurrentAirQuality(
        us_aqi=165,
    )
    assert "Unhealthy" in aqi.aqi_health_descriptor


def test_space_weather_model_validation():
    sw = SpaceWeatherTelemetry(
        kp_index=7.33,
    )
    assert sw.noaa_scale == "G3 (Strong)"


def test_geocoding_model_validation():
    resp = GeocodingResponse(
        results=[
            GeocodingLocation(
                name="Nairobi",
                latitude=-1.286389,
                longitude=36.817223,
                country="Kenya",
            )
        ]
    )
    assert len(resp.results) == 1
    assert resp.results[0].country == "Kenya"
