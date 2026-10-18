"""3-route guarantee and ORS → OSRM fallback (mocked providers)."""

from unittest.mock import patch

from apps.geo.polyline import LatLon
from apps.routing.providers.ors import ORSAuthError, ORSRateLimitError
from apps.routing.service import get_route_alternatives
from apps.routing.types import RawRoute


def _route(lon_shift: float, duration: float, provider: str = "test") -> RawRoute:
    return RawRoute(
        geometry=[
            LatLon(41.88, -87.63),
            LatLon(41.88 + lon_shift * 0.1, -87.63 + lon_shift),
            LatLon(42.33, -83.05 + lon_shift),
        ],
        distance_m=400_000 + abs(lon_shift) * 1000,
        duration_s=duration,
        provider=provider,
        summary=f"shift={lon_shift}",
    )


def test_ors_auth_falls_back_to_osrm():
    origin = LatLon(41.88, -87.63)
    dest = LatLon(42.33, -83.05)
    osrm_routes = [_route(0.0, 3000, "osrm"), _route(1.5, 3200, "osrm"), _route(-1.5, 3400, "osrm")]

    with (
        patch("apps.routing.service.ors.route", side_effect=ORSAuthError("no key")),
        patch("apps.routing.service.osrm.route", return_value=osrm_routes) as osrm_mock,
    ):
        routes, degraded = get_route_alternatives(origin, dest)

    assert "ors_auth" in degraded
    assert osrm_mock.called
    assert 1 <= len(routes) <= 3


def test_ors_rate_limit_falls_back_to_osrm():
    origin = LatLon(41.88, -87.63)
    dest = LatLon(42.33, -83.05)

    with (
        patch("apps.routing.service.ors.route", side_effect=ORSRateLimitError("429")),
        patch(
            "apps.routing.service.osrm.route",
            return_value=[_route(0.0, 3000, "osrm")],
        ),
    ):
        routes, degraded = get_route_alternatives(origin, dest)

    assert "ors_rate_limit" in degraded
    assert routes


def test_via_top_up_when_primary_returns_one():
    origin = LatLon(41.88, -87.63)
    dest = LatLon(42.33, -83.05)
    primary = [_route(0.0, 3000, "ors")]
    via_a = [_route(2.0, 3500, "ors")]
    via_b = [_route(-2.0, 3600, "ors")]

    call_n = {"n": 0}

    def ors_side_effect(*_args, **kwargs):
        call_n["n"] += 1
        if "via" in kwargs and kwargs["via"]:
            # Alternate distinct via responses
            return via_a if call_n["n"] % 2 == 0 else via_b
        return primary

    with patch("apps.routing.service.ors.route", side_effect=ors_side_effect):
        routes, degraded = get_route_alternatives(origin, dest)

    assert len(routes) == 3
    assert "fewer_than_3_routes" not in degraded


def test_fewer_than_3_flag_when_only_one_distinct():
    origin = LatLon(41.88, -87.63)
    dest = LatLon(42.33, -83.05)
    only = [_route(0.0, 3000, "osrm")]

    with (
        patch("apps.routing.service.ors.route", side_effect=ORSAuthError("no key")),
        patch("apps.routing.service.osrm.route", return_value=only),
    ):
        routes, degraded = get_route_alternatives(origin, dest)

    assert len(routes) == 1
    assert "fewer_than_3_routes" in degraded
