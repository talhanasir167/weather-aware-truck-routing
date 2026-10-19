"""Guards against quadratic blowups that previously timed out the worker.

Planning ran on a shared 0.1-CPU instance, so geometry work had to stay
linear in vertex count. These tests fail loudly if it goes quadratic again.
"""

from __future__ import annotations

import time

from apps.geo.polyline import LatLon, cumulative_distances_mi
from apps.routing.dedupe import dedupe_routes, overlap_ratio
from apps.routing.eta import duration_axis, duration_on_axis
from apps.routing.sampling import build_checkpoints
from apps.routing.types import RawRoute

DEPARTURE = "2026-10-20T07:00:00Z"


def _route(vertices: int, lon_shift: float = 0.0, duration_s: float = 150_000.0) -> RawRoute:
    geometry = [
        LatLon(
            lat=34.05 + i * (6.7 / vertices) + lon_shift * 0.2,
            lon=-118.24 + i * (44.2 / vertices) + lon_shift,
        )
        for i in range(vertices)
    ]
    cum_mi = cumulative_distances_mi(geometry)
    cum_s = [d / cum_mi[-1] * duration_s for d in cum_mi]
    return RawRoute(
        geometry=geometry,
        distance_m=4_500_000,
        duration_s=duration_s,
        provider="test",
        cum_distance_mi=cum_mi,
        cum_duration_s=cum_s,
    )


def test_dedupe_cost_is_flat_in_vertex_count():
    """Dedupe samples a fixed number of points, so 10x vertices must not cost 10x."""
    small = [_route(1_000), _route(1_000, 0.03), _route(1_000, 2.5)]
    large = [_route(10_000), _route(10_000, 0.03), _route(10_000, 2.5)]

    start = time.perf_counter()
    dedupe_routes(small)
    small_s = time.perf_counter() - start

    start = time.perf_counter()
    dedupe_routes(large)
    large_s = time.perf_counter() - start

    assert large_s < max(small_s * 4, 0.25)


def test_dedupe_still_separates_and_merges_routes():
    near_duplicate = _route(2_000, 0.01, duration_s=151_000)
    distinct = _route(2_000, 3.0, duration_s=160_000)
    base = _route(2_000, 0.0, duration_s=150_000)

    assert overlap_ratio(base, near_duplicate) > 0.7
    assert overlap_ratio(base, distinct) < 0.7
    assert len(dedupe_routes([base, near_duplicate, distinct])) == 2


def test_build_checkpoints_scales_with_checkpoints_not_vertices():
    route = _route(12_000)
    start = time.perf_counter()
    checkpoints = build_checkpoints(
        route.geometry,
        25,
        DEPARTURE,
        cum_distance_mi=route.cum_distance_mi,
        cum_duration_s=route.cum_duration_s,
    )
    elapsed = time.perf_counter() - start

    assert len(checkpoints) >= 100
    assert elapsed < 0.5
    assert [c.eta_utc for c in checkpoints] == sorted(c.eta_utc for c in checkpoints)


def test_duration_axis_matches_linear_interpolation():
    dists = [0.0, 50.0, 100.0]
    durs = [0.0, 3600.0, 7200.0]
    assert duration_on_axis(25.0, dists, durs) == 1800.0
    assert duration_on_axis(0.0, dists, durs) == 0.0
    assert duration_on_axis(200.0, dists, durs) == 7200.0


def test_duration_axis_falls_back_to_uniform_speed():
    geometry = [LatLon(40, -90), LatLon(40, -89)]
    dists, durs = duration_axis(geometry, cum_distance_mi=[0.0, 55.0])
    assert durs[-1] == 3600.0
    assert dists[-1] == 55.0
