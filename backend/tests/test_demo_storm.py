from apps.risk.bands import RiskBand
from apps.risk.scoring import checkpoint_band
from apps.weather.demo_storm import apply_storm_to_samples, boost_heatmap_frame
from apps.weather.types import WeatherSample


def _calm(n=10):
    return [
        WeatherSample(
            lat=41.0,
            lon=-87.0 + i * 0.1,
            hour_utc="2026-10-18T12:00:00Z",
            wind_mph=8,
            wind_gusts_mph=10,
            rain_in_hr=0,
            snow_in_hr=0,
        )
        for i in range(n)
    ]


def test_storm_raises_middle_checkpoints():
    calm = _calm(12)
    stormed = apply_storm_to_samples(calm, route_index=2)
    # Ends stay calm-ish; middle is elevated
    assert stormed[0].wind_mph <= 15
    mid = stormed[len(stormed) // 2]
    assert mid.wind_mph >= 45
    band = checkpoint_band(mid.wind_mph, mid.rain_in_hr, mid.snow_in_hr, 20_000)
    assert band >= RiskBand.HIGH


def test_routes_differ_in_severity():
    a = apply_storm_to_samples(_calm(12), route_index=0)
    c = apply_storm_to_samples(_calm(12), route_index=2)
    assert c[6].wind_mph > a[6].wind_mph


def test_heatmap_boost():
    risk = [0.0] * 20
    wind = [5.0] * 20
    rain = [0.0] * 20
    snow = [0.0] * 20
    boost_heatmap_frame(risk, wind, rain, snow, hour_index=12)
    assert max(risk) >= 2.0
    assert max(wind) > 30
