"""Build a corridor grid along the union of route geometries."""

from __future__ import annotations

from apps.geo.distance import bearing_deg, offset_point
from apps.geo.polyline import LatLon, cumulative_distances_mi


def _sample_centerline(routes_geom: list[list[LatLon]], spacing_mi: float = 20.0) -> list[LatLon]:
    """Use the longest route as the corridor centerline, sampled every spacing_mi."""
    if not routes_geom:
        return []
    longest = max(routes_geom, key=lambda g: cumulative_distances_mi(g)[-1] if g else 0)
    if not longest:
        return []
    dists = cumulative_distances_mi(longest)
    total = dists[-1]
    if total <= 0:
        return [longest[0]]

    targets = [0.0]
    d = spacing_mi
    while d < total:
        targets.append(d)
        d += spacing_mi
    if targets[-1] < total - 1e-3:
        targets.append(total)

    points: list[LatLon] = []
    vi = 0
    for t in targets:
        while vi < len(dists) - 1 and dists[vi + 1] < t:
            vi += 1
        points.append(longest[min(vi, len(longest) - 1)])
    return points


def build_corridor_grid(
    routes_geom: list[list[LatLon]],
    spacing_mi: float = 20.0,
    lateral_offsets_mi: tuple[float, ...] = (-25.0, 0.0, 25.0),
    max_points: int = 150,
) -> list[LatLon]:
    """Return corridor grid points (centerline + lateral offsets), capped at max_points."""
    center = _sample_centerline(routes_geom, spacing_mi=spacing_mi)
    if not center:
        return []

    grid: list[LatLon] = []
    for i, pt in enumerate(center):
        if i < len(center) - 1:
            br = bearing_deg(pt.lat, pt.lon, center[i + 1].lat, center[i + 1].lon)
        elif i > 0:
            br = bearing_deg(center[i - 1].lat, center[i - 1].lon, pt.lat, pt.lon)
        else:
            br = 0.0
        left = (br - 90) % 360
        right = (br + 90) % 360
        for off in lateral_offsets_mi:
            if off == 0:
                grid.append(pt)
            else:
                bearing = left if off < 0 else right
                lat, lon = offset_point(pt.lat, pt.lon, bearing, abs(off))
                grid.append(LatLon(lat=lat, lon=lon))

    if len(grid) > max_points:
        step = max(1, len(grid) // max_points)
        grid = grid[::step][:max_points]
    return grid
