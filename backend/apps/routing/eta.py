"""ETA interpolation from cumulative distance/duration annotations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apps.geo.polyline import LatLon, cumulative_distances_mi


def _parse_aware(iso: str) -> datetime:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("departure must be timezone-aware ISO 8601")
    return dt.astimezone(timezone.utc)


def _lerp(x0: float, y0: float, x1: float, y1: float, x: float) -> float:
    if x1 <= x0:
        return y0
    t = (x - x0) / (x1 - x0)
    return y0 + t * (y1 - y0)


def duration_at_distance(
    dist_mi: float,
    geometry: list[LatLon],
    cum_distance_mi: list[float] | None = None,
    cum_duration_s: list[float] | None = None,
    total_duration_s: float | None = None,
) -> float:
    """Interpolate duration (seconds) at a given distance along the route."""
    dists = cum_distance_mi if cum_distance_mi else cumulative_distances_mi(geometry)
    total_mi = dists[-1] if dists else 0.0

    if total_mi <= 0:
        return 0.0

    if cum_duration_s and len(cum_duration_s) == len(dists):
        durs = cum_duration_s
    else:
        # Uniform speed fallback
        total_dur = total_duration_s if total_duration_s is not None else 0.0
        if total_dur <= 0:
            # assume 55 mph average
            total_dur = (total_mi / 55.0) * 3600.0
        durs = [d / total_mi * total_dur for d in dists]

    if dist_mi <= 0:
        return 0.0
    if dist_mi >= total_mi:
        return durs[-1]

    # Find bracketing vertices
    for i in range(len(dists) - 1):
        if dists[i] <= dist_mi <= dists[i + 1]:
            return _lerp(dists[i], durs[i], dists[i + 1], durs[i + 1], dist_mi)
    return durs[-1]


def eta_at_distance(
    dist_mi: float,
    departure_utc_iso: str,
    geometry: list[LatLon],
    cum_distance_mi: list[float] | None = None,
    cum_duration_s: list[float] | None = None,
    total_duration_s: float | None = None,
) -> tuple[float, str]:
    """Return (duration_s, eta_iso_utc) for a distance along the route."""
    dep = _parse_aware(departure_utc_iso)
    dur = duration_at_distance(
        dist_mi, geometry, cum_distance_mi, cum_duration_s, total_duration_s
    )
    eta = dep + timedelta(seconds=dur)
    return dur, eta.isoformat().replace("+00:00", "Z")
