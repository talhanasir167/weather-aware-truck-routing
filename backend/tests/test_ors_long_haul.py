"""ORS free-tier: alternative_routes rejected on long hauls → retry single route."""

from unittest.mock import MagicMock, patch

from apps.geo.polyline import LatLon
from apps.routing.providers import ors


def _geojson_feature(lon0=-87.63, lat0=41.88, lon1=-83.05, lat1=42.33, dist=400_000, dur=18_000):
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[lon0, lat0], [lon1, lat1]],
                },
                "properties": {"summary": {"distance": dist, "duration": dur}},
            }
        ],
    }


def test_ors_retries_without_alternatives_on_2004():
    origin = LatLon(41.88, -87.63)
    dest = LatLon(42.33, -83.05)

    bad = MagicMock()
    bad.status_code = 400
    bad.json.return_value = {
        "error": {
            "code": 2004,
            "message": "approximated route distance must not be greater than 100000.0 meters",
        }
    }

    good = MagicMock()
    good.status_code = 200
    good.raise_for_status = MagicMock()
    good.json.return_value = _geojson_feature()

    with (
        patch.object(ors.settings, "ORS_API_KEY", "test-key"),
        patch.object(ors, "_post_directions", side_effect=[bad, good]) as post,
    ):
        routes = ors.route(origin, dest, alternatives=3)

    assert len(routes) == 1
    assert routes[0].provider == "ors"
    assert post.call_count == 2
    # Second call must not request alternative_routes
    second_body = post.call_args_list[1].args[0]
    assert "alternative_routes" not in second_body


def test_ors_auth_still_raises():
    origin = LatLon(41.88, -87.63)
    dest = LatLon(42.33, -83.05)
    resp = MagicMock()
    resp.status_code = 401
    with (
        patch.object(ors.settings, "ORS_API_KEY", "bad"),
        patch.object(ors, "_post_directions", return_value=resp),
    ):
        try:
            ors.route(origin, dest)
            assert False, "expected ORSAuthError"
        except ors.ORSAuthError:
            pass
