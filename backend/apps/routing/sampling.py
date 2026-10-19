"""Exact-distance checkpoint sampling along a route geometry."""

from __future__ import annotations

from datetime import timedelta

from apps.geo.polyline import LatLon, cumulative_distances_mi

from .types import Checkpoint


def _interpolate(
    a: LatLon, b: LatLon, dist_a: float, dist_b: float, target: float
) -> LatLon:
    """Linear interpolate lat/lon between a and b by distance."""
    if dist_b <= dist_a:
        return a
    t = (target - dist_a) / (dist_b - dist_a)
    t = max(0.0, min(1.0, t))
    return LatLon(lat=a.lat + t * (b.lat - a.lat), lon=a.lon + t * (b.lon - a.lon))


def sample_checkpoints(
    geometry: list[LatLon],
    interval_mi: float,
    cum_distance_mi: list[float] | None = None,
) -> list[tuple[LatLon, float]]:
    """Sample points every `interval_mi` along the route, always including destination.

    Returns list of (point, distance_from_start_mi).
    """
    if not geometry:
        return []
    if interval_mi <= 0:
        raise ValueError("interval_mi must be positive")

    dists = cum_distance_mi if cum_distance_mi else cumulative_distances_mi(geometry)
    if len(dists) != len(geometry):
        dists = cumulative_distances_mi(geometry)

    total = dists[-1]
    if total <= 0:
        return [(geometry[0], 0.0)]

    targets = [0.0]
    d = interval_mi
    while d < total - 1e-6:
        targets.append(d)
        d += interval_mi
    if targets[-1] < total - 1e-6:
        targets.append(total)
    elif abs(targets[-1] - total) > 1e-6:
        # last target somehow past total — replace
        targets[-1] = total

    # Deduplicate near-identical targets
    clean: list[float] = []
    for t in targets:
        if not clean or abs(t - clean[-1]) > 1e-4:
            clean.append(t)

    result: list[tuple[LatLon, float]] = []
    vi = 0
    for target in clean:
        while vi < len(dists) - 1 and dists[vi + 1] < target:
            vi += 1
        if abs(dists[vi] - target) < 1e-6:
            pt = geometry[vi]
        elif vi < len(geometry) - 1:
            pt = _interpolate(geometry[vi], geometry[vi + 1], dists[vi], dists[vi + 1], target)
        else:
            pt = geometry[-1]
        result.append((pt, target))
    return result


def build_checkpoints(
    geometry: list[LatLon],
    interval_mi: float,
    departure_utc_iso: str,
    cum_distance_mi: list[float] | None = None,
    cum_duration_s: list[float] | None = None,
) -> list[Checkpoint]:
    """Sample checkpoints and attach ETAs via duration interpolation."""
    from .eta import duration_axis, duration_on_axis, parse_departure

    samples = sample_checkpoints(geometry, interval_mi, cum_distance_mi)
    # Resolve distance/duration axis once, then interpolate each checkpoint.
    dists, durs = duration_axis(geometry, cum_distance_mi, cum_duration_s)
    departure = parse_departure(departure_utc_iso)

    checkpoints: list[Checkpoint] = []
    for i, (pt, dist_mi) in enumerate(samples):
        dur_s = duration_on_axis(dist_mi, dists, durs)
        eta_iso = (departure + timedelta(seconds=dur_s)).isoformat().replace("+00:00", "Z")
        checkpoints.append(
            Checkpoint(
                index=i,
                lat=pt.lat,
                lon=pt.lon,
                distance_mi=round(dist_mi, 3),
                eta_utc=eta_iso,
                duration_from_start_s=dur_s,
            )
        )
    return checkpoints
