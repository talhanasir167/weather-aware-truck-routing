from apps.geo.polyline import LatLon
from apps.risk.aggregate import midpoint_segment_miles
from apps.routing.sampling import sample_checkpoints


def _straight_line(miles: float, n_vertices: int = 50) -> list[LatLon]:
    """Approximate eastward straight line ~`miles` long starting at (40, -90)."""
    # 1 deg lon ≈ 53 mi at lat 40
    deg = miles / 53.0
    return [
        LatLon(lat=40.0, lon=-90.0 + deg * i / (n_vertices - 1)) for i in range(n_vertices)
    ]


def test_interval_25_count():
    geom = _straight_line(100)
    samples = sample_checkpoints(geom, 25)
    distances = [d for _, d in samples]
    assert distances[0] == 0.0
    assert abs(distances[-1] - 100) < 2.0  # haversine approx
    # 0, 25, 50, 75, ~100
    assert len(samples) >= 5


def test_destination_always_included():
    geom = _straight_line(40)
    samples = sample_checkpoints(geom, 25)
    assert samples[-1][0].lat == geom[-1].lat
    assert samples[-1][0].lon == geom[-1].lon


def test_short_route():
    geom = _straight_line(5)
    samples = sample_checkpoints(geom, 25)
    assert len(samples) == 2  # origin + destination
    assert samples[0][1] == 0.0


def test_zero_length():
    geom = [LatLon(40, -90), LatLon(40, -90)]
    samples = sample_checkpoints(geom, 25)
    assert len(samples) == 1


def test_segment_miles_sum():
    distances = [0, 25, 50, 75, 100]
    segs = midpoint_segment_miles(distances, 100.0)
    assert abs(sum(segs) - 100.0) < 0.01
    assert len(segs) == 5


def test_single_checkpoint_owns_all():
    segs = midpoint_segment_miles([0.0], 42.0)
    assert segs == [42.0]
