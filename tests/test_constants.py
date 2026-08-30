"""Pin constants so renames don\'t silently break APIs."""

from core import constants


def test_storage_keys_prefix():
    for k in [
        constants.STORAGE_THEME,
        constants.STORAGE_BOOKMARKS,
        constants.STORAGE_RECENT_SEARCHES,
        constants.STORAGE_ONBOARDING_DONE,
    ]:
        assert k.startswith("asase.")


def test_endpoint_urls():
    assert "earthquake.usgs.gov" in constants.USGS_EARTHQUAKES_DAY
    assert "earthquake.usgs.gov" in constants.USGS_EARTHQUAKES_HOUR
    assert "eonet.gsfc.nasa.gov" in constants.NASA_EONET_EVENTS
    assert "open-meteo.com" in constants.OPEN_METEO_FORECAST
    assert "services.swpc.noaa.gov" in constants.NOAA_SWPC_KP_INDEX


def test_eonet_category_map():
    assert constants.EONET_CATEGORY_MAP["wildfire"] == "wildfires"
    assert constants.EONET_CATEGORY_MAP["storm"] == "severeStorms"
    assert constants.EONET_CATEGORY_MAP["fire"] == "wildfires"


def test_app_name():
    assert constants.APP_NAME == "Asase"
