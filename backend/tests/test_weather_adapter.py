import httpx
import respx
from django.test import override_settings

from apps.weather.providers import open_meteo

SAMPLE_PAYLOAD = {
    "latitude": 41.88,
    "longitude": -87.63,
    "hourly": {
        "time": ["2026-10-17T12:00", "2026-10-17T13:00", "2026-10-17T14:00"],
        "wind_speed_10m": [10.0, 30.0, 60.0],
        "wind_gusts_10m": [15.0, 40.0, 70.0],
        "rain": [0.0, 0.2, 0.0],
        "snowfall": [0.0, 0.0, 0.0],
        "precipitation": [0.0, 0.2, 0.0],
        "weather_code": [0, 61, 0],
    },
}


@respx.mock
@override_settings(OPEN_METEO_BASE_URL="https://api.open-meteo.com", HTTP_TIMEOUT_S=5)
def test_fetch_and_sample():
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAYLOAD)
    )
    payloads = open_meteo.fetch_hourly([(41.88, -87.63)], forecast_days=2)
    assert len(payloads) == 1
    sample = open_meteo.sample_at_hour(payloads[0], "2026-10-17T13:30:00Z")
    assert sample is not None
    assert sample["wind_mph"] == 30.0
    assert sample["rain_in_hr"] == 0.2


@respx.mock
@override_settings(OPEN_METEO_BASE_URL="https://api.open-meteo.com", HTTP_TIMEOUT_S=5)
def test_missing_hour_returns_none_or_nearest():
    respx.get("https://api.open-meteo.com/v1/forecast").mock(
        return_value=httpx.Response(200, json=SAMPLE_PAYLOAD)
    )
    payloads = open_meteo.fetch_hourly([(41.88, -87.63)])
    # Far future — beyond 90 min of available hours
    sample = open_meteo.sample_at_hour(payloads[0], "2026-11-01T00:00:00Z")
    assert sample is None
