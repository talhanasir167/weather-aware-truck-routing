"""ETA interpolation from cumulative distance/duration annotations."""

from __future__ import annotations

from bisect import bisect_right
from datetime import datetime, timedelta, timezone

from apps.geo.polyline import LatLon, cumulative_distances_mi


def parse_departure(iso: str) -> datetime:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("departure must be timezone-aware ISO 8601")
    return dt.astimezone(timezone.utc)


def _lerp(x0: float, y0: float, x1: float, y1: float, x: float) -> float:
    if x1 <= x0:
        return y0
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def duration_axis(
    geometry: list[LatLon],
    cum_distance_mi: list[float] | None = None,
    cum_duration_s: list[float] | None = None,
    total_duration_s: float | None = None,
) -> tuple[list[float], list[float]]:
    """Build the (cumulative distance, cumulative duration) axis for a route.

    Resolve this once per route — rebuilding it per checkpoint is quadratic in
    geometry size.
    """
    dists = cum_distance_mi if cum_distance_mi else cumulative_distances_mi(geometry)
    total_mi = dists[-1] if dists else 0.0
    if total_mi <= 0:
        return dists, []

    if cum_duration_s and len(cum_duration_s) == len(dists):
        return dists, cum_duration_s

    # Uniform speed fallback (assume 55 mph average when duration is unknown)
    total_dur = total_duration_s if total_duration_s is not None else 0.0
    if total_dur <= 0:
        total_dur = (total_mi / 55.0) * 3600.0
    return dists, [d / total_mi * total_dur for d in dists]


def duration_on_axis(dist_mi: float, dists: list[float], durs: list[float]) -> float:
    """Interpolate duration (seconds) at a distance using a prebuilt axis."""
    if not durs or not dists:
        return 0.0
    total_mi = dists[-1]
    if total_mi <= 0 or dist_mi <= 0:
        return 0.0
    if dist_mi >= total_mi:
        return durs[-1]
    i = max(bisect_right(dists, dist_mi) - 1, 0)
    if i >= len(dists) - 1:
        return durs[-1]
    return _lerp(dists[i], durs[i], dists[i + 1], durs[i + 1], dist_mi)


def duration_at_distance(
    dist_mi: float,
    geometry: list[LatLon],
    cum_distance_mi: list[float] | None = None,
    cum_duration_s: list[float] | None = None,
    total_duration_s: float | None = None,
) -> float:
    """Interpolate duration (seconds) at a given distance along the route."""
    dists, durs = duration_axis(geometry, cum_distance_mi, cum_duration_s, total_duration_s)
    return duration_on_axis(dist_mi, dists, durs)


def eta_at_distance(
    dist_mi: float,
    departure_utc_iso: str,
    geometry: list[LatLon],
    cum_distance_mi: list[float] | None = None,
    cum_duration_s: list[float] | None = None,
    total_duration_s: float | None = None,
) -> tuple[float, str]:
    """Return (duration_s, eta_iso_utc) for a distance along the route."""
    dep = parse_departure(departure_utc_iso)
    dur = duration_at_distance(
        dist_mi, geometry, cum_distance_mi, cum_duration_s, total_duration_s
    )
    eta = dep + timedelta(seconds=dur)
    return dur, eta.isoformat().replace("+00:00", "Z")
