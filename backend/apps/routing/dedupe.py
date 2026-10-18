"""Geometry overlap deduplication for candidate routes."""

from __future__ import annotations

from apps.geo.distance import haversine_mi
from apps.geo.polyline import LatLon, cumulative_distances_mi
from apps.routing.types import RawRoute


def _sample_evenly(geometry: list[LatLon], n: int = 40) -> list[LatLon]:
    if len(geometry) <= n:
        return geometry
    dists = cumulative_distances_mi(geometry)
    total = dists[-1] or 1.0
    targets = [i * total / (n - 1) for i in range(n)]
    out: list[LatLon] = []
    vi = 0
    for t in targets:
        while vi < len(dists) - 1 and dists[vi + 1] < t:
            vi += 1
        out.append(geometry[vi])
    return out


def overlap_ratio(a: RawRoute, b: RawRoute, threshold_mi: float = 2.0) -> float:
    """Fraction of A's sample points that lie within threshold_mi of some point on B."""
    sa = _sample_evenly(a.geometry)
    sb = _sample_evenly(b.geometry)
    if not sa:
        return 0.0
    close = 0
    for pa in sa:
        if any(haversine_mi(pa.lat, pa.lon, pb.lat, pb.lon) <= threshold_mi for pb in sb):
            close += 1
    return close / len(sa)


def dedupe_routes(candidates: list[RawRoute], max_overlap: float = 0.70) -> list[RawRoute]:
    """Keep routes in duration order, rejecting those that overlap > max_overlap with kept ones."""
    ordered = sorted(candidates, key=lambda r: r.duration_s)
    kept: list[RawRoute] = []
    for cand in ordered:
        if any(overlap_ratio(cand, k) > max_overlap for k in kept):
            continue
        kept.append(cand)
    return kept
