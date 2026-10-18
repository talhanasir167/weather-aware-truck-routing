from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from django.test import override_settings

from apps.geo.polyline import LatLon
from apps.heatmap.corridor import build_corridor_grid
from apps.heatmap.service import build_heatmap
from apps.planner.models import RoutePlan, Trip
from apps.weather.types import WeatherSample


def test_corridor_cap():
    geom = [LatLon(40, -90 + i * 0.5) for i in range(40)]
    grid = build_corridor_grid([geom], spacing_mi=10, max_points=50)
    assert len(grid) <= 50
    assert len(grid) > 0


@pytest.mark.django_db
@override_settings(HEATMAP_MAX_POINTS=30)
def test_heatmap_49_frames():
    trip = Trip.objects.create(
        origin_label="A",
        origin_lat=41.88,
        origin_lon=-87.63,
        destination_label="B",
        destination_lat=42.33,
        destination_lon=-83.05,
        departure_utc=datetime(2026, 10, 17, 12, 0, tzinfo=timezone.utc),
        load_lb=20000,
        interval_mi=25,
    )
    RoutePlan.objects.create(
        trip=trip,
        route_key="route_0",
        provider="test",
        distance_m=400_000,
        duration_s=18000,
        geometry=[[-87.63, 41.88], [-85.0, 42.0], [-83.05, 42.33]],
        metrics={},
        is_recommended=True,
        rank=0,
    )

    def fake_fetch(points):
        samples = [
            WeatherSample(
                lat=lat,
                lon=lon,
                hour_utc=eta,
                wind_mph=10,
                wind_gusts_mph=15,
                rain_in_hr=0,
                snow_in_hr=0,
            )
            for lat, lon, eta in points
        ]
        return samples, {"cache_hit_ratio": 0.0, "fetched": len(points), "requested": len(points)}

    with patch("apps.heatmap.service.fetch_for_checkpoints", side_effect=fake_fetch):
        data = build_heatmap(trip)

    assert len(data["hours"]) == 49
    assert len(data["frames"]["risk"]) == 49
    assert len(data["frames"]["risk"]) == len(data["hours"])
    n = len(data["grid_points"])
    assert n <= 30
    assert all(len(row) == n for row in data["frames"]["risk"])
