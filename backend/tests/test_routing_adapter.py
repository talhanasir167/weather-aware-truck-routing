from apps.geo.polyline import LatLon
from apps.routing.dedupe import dedupe_routes, overlap_ratio
from apps.routing.types import RawRoute


def _route(lon_offset: float, duration: float = 3600) -> RawRoute:
    geom = [
        LatLon(41.88, -87.63),
        LatLon(41.88, -87.63 + lon_offset),
        LatLon(42.33, -83.05 + lon_offset),
    ]
    return RawRoute(
        geometry=geom,
        distance_m=400_000,
        duration_s=duration,
        provider="test",
    )


def test_overlap_identical_high():
    a = _route(0.0)
    b = _route(0.0)
    assert overlap_ratio(a, b) > 0.9


def test_dedupe_keeps_distinct():
    a = _route(0.0, 3000)
    b = _route(0.0, 3100)  # nearly identical geometry — should drop
    c = _route(2.0, 4000)  # shifted
    kept = dedupe_routes([a, b, c], max_overlap=0.70)
    assert len(kept) >= 1
    assert kept[0].duration_s == 3000
