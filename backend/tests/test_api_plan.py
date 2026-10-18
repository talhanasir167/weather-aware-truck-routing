from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.geo.polyline import LatLon
from apps.routing.types import RawRoute
from apps.weather.types import WeatherSample


@pytest.fixture
def client():
    return APIClient()


def test_healthz(client):
    resp = client.get("/api/v1/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_status_reports_ors_and_demo_flags(client, settings):
    settings.ORS_API_KEY = ""
    resp = client.get("/api/v1/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ors_configured"] is False
    assert body["routing"]["primary"] == "osrm_fallback"
    assert body["demo_storm_available"] is True

    settings.ORS_API_KEY = "test-key"
    resp2 = client.get("/api/v1/status")
    assert resp2.json()["ors_configured"] is True
    assert resp2.json()["routing"]["primary"] == "openrouteservice_driving-hgv"


def test_plan_validation_bad_load(client):
    resp = client.post(
        "/api/v1/trips/plan",
        {
            "origin": "Chicago, IL",
            "destination": "Detroit, MI",
            "departure": "2026-10-17T12:00:00Z",
            "load_lb": 0,
        },
        format="json",
    )
    assert resp.status_code == 400


def test_plan_rejects_naive_departure(client):
    resp = client.post(
        "/api/v1/trips/plan",
        {
            "origin": "Chicago, IL",
            "destination": "Detroit, MI",
            "departure": "2026-10-17T12:00:00",
            "load_lb": 20000,
            "origin_lat": 41.88,
            "origin_lon": -87.63,
            "destination_lat": 42.33,
            "destination_lon": -83.05,
        },
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_plan_happy_path(client):
    geom = [
        LatLon(41.88, -87.63),
        LatLon(42.0, -85.0),
        LatLon(42.33, -83.05),
    ]
    raw = [
        RawRoute(
            geometry=geom,
            distance_m=400_000,
            duration_s=18000,
            cum_distance_mi=[0, 125, 250],
            cum_duration_s=[0, 9000, 18000],
            provider="test",
            summary="test route",
        )
    ]

    def fake_wx(points):
        samples = [
            WeatherSample(lat=la, lon=lo, hour_utc=e, wind_mph=10, wind_gusts_mph=12, rain_in_hr=0, snow_in_hr=0)
            for la, lo, e in points
        ]
        return samples, {"cache_hit_ratio": 1.0, "fetched": 0, "requested": len(points)}

    with (
        patch("apps.planner.service.get_route_alternatives", return_value=(raw, [])),
        patch("apps.planner.service.fetch_for_checkpoints", side_effect=fake_wx),
    ):
        resp = client.post(
            "/api/v1/trips/plan",
            {
                "origin": "Chicago, IL",
                "destination": "Detroit, MI",
                "departure": "2026-10-17T12:00:00Z",
                "load_lb": 20000,
                "interval_mi": 50,
                "origin_lat": 41.88,
                "origin_lon": -87.63,
                "destination_lat": 42.33,
                "destination_lon": -83.05,
            },
            format="json",
        )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert "id" in body
    assert len(body["routes"]) == 1
    assert body["recommendation"]["route_id"] == "route_0"
    assert body["routes"][0]["checkpoints"]


@pytest.mark.django_db
def test_plan_demo_storm_sets_meta_flag(client):
    geom = [
        LatLon(41.88, -87.63),
        LatLon(42.0, -85.0),
        LatLon(42.33, -83.05),
    ]
    raw = [
        RawRoute(
            geometry=geom,
            distance_m=400_000,
            duration_s=18000,
            cum_distance_mi=[0, 125, 250],
            cum_duration_s=[0, 9000, 18000],
            provider="test",
        )
    ]

    def fake_wx(points):
        samples = [
            WeatherSample(
                lat=la, lon=lo, hour_utc=e, wind_mph=8, wind_gusts_mph=10, rain_in_hr=0, snow_in_hr=0
            )
            for la, lo, e in points
        ]
        return samples, {"cache_hit_ratio": 1.0, "fetched": 0, "requested": len(points)}

    with (
        patch("apps.planner.service.get_route_alternatives", return_value=(raw, [])),
        patch("apps.planner.service.fetch_for_checkpoints", side_effect=fake_wx),
    ):
        resp = client.post(
            "/api/v1/trips/plan",
            {
                "origin": "Chicago, IL",
                "destination": "Minneapolis, MN",
                "departure": "2026-10-17T12:00:00Z",
                "load_lb": 20000,
                "interval_mi": 50,
                "demo_storm": True,
                "origin_lat": 41.88,
                "origin_lon": -87.63,
                "destination_lat": 44.98,
                "destination_lon": -93.27,
            },
            format="json",
        )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["meta"]["demo_storm"] is True
    # Storm overlay should elevate at least one mid-route checkpoint above Low
    bands = {cp["band"] for cp in body["routes"][0]["checkpoints"]}
    assert bands - {"Low"}
