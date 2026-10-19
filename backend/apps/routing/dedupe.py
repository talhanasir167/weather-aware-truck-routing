"""Geometry overlap deduplication for candidate routes.

Overlap is a proximity test, so points are projected to a local flat
(x, y) grid in miles once per route. Re-running haversine over full
provider geometries here is what made planning slow on small instances.
"""

from __future__ import annotations

import math

from apps.geo.polyline import LatLon
from apps.routing.types import RawRoute

SAMPLES = 40
_MI_PER_DEG = 69.0


def _sample_evenly(
    geometry: list[LatLon],
    n: int = SAMPLES,
    cum_distance_mi: list[float] | None = None,
) -> list[LatLon]:
    """Evenly spaced sample of a geometry.

    Uses provider cumulative distances when available (already computed, so
    free) and otherwise falls back to vertex-index spacing.
    """
    if len(geometry) <= n:
        return list(geometry)
    if cum_distance_mi and len(cum_distance_mi) == len(geometry) and cum_distance_mi[-1] > 0:
        total = cum_distance_mi[-1]
        out: list[LatLon] = []
        vi = 0
        for i in range(n):
            target = i * total / (n - 1)
            while vi < len(cum_distance_mi) - 1 and cum_distance_mi[vi + 1] < target:
                vi += 1
            out.append(geometry[vi])
        return out
    step = (len(geometry) - 1) / (n - 1)
    last = len(geometry) - 1
    return [geometry[min(int(round(i * step)), last)] for i in range(n)]


def _project(points: list[LatLon]) -> list[tuple[float, float]]:
    """Project lat/lon to approximate miles (x east, y north)."""
    out: list[tuple[float, float]] = []
    for p in points:
        x = p.lon * _MI_PER_DEG * math.cos(math.radians(p.lat))
        out.append((x, p.lat * _MI_PER_DEG))
    return out


def _projected_samples(route: RawRoute) -> list[tuple[float, float]]:
    return _project(_sample_evenly(route.geometry, cum_distance_mi=route.cum_distance_mi or None))


def _overlap(
    sa: list[tuple[float, float]],
    sb: list[tuple[float, float]],
    threshold_mi: float,
) -> float:
    if not sa:
        return 0.0
    limit = threshold_mi * threshold_mi
    close = 0
    for ax, ay in sa:
        for bx, by in sb:
            dx = ax - bx
            if dx > threshold_mi or dx < -threshold_mi:
                continue
            dy = ay - by
            if dx * dx + dy * dy <= limit:
                close += 1
                break
    return close / len(sa)


def overlap_ratio(a: RawRoute, b: RawRoute, threshold_mi: float = 2.0) -> float:
    """Fraction of A's sample points that lie within threshold_mi of some point on B."""
    return _overlap(_projected_samples(a), _projected_samples(b), threshold_mi)


def dedupe_routes(candidates: list[RawRoute], max_overlap: float = 0.70) -> list[RawRoute]:
    """Keep routes in duration order, rejecting those that overlap > max_overlap with kept ones."""
    ordered = sorted(candidates, key=lambda r: r.duration_s)
    kept: list[RawRoute] = []
    kept_samples: list[list[tuple[float, float]]] = []
    for cand in ordered:
        samples = _projected_samples(cand)
        if any(_overlap(samples, ks, 2.0) > max_overlap for ks in kept_samples):
            continue
        kept.append(cand)
        kept_samples.append(samples)
    return kept
