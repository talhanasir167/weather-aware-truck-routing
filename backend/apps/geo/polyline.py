"""Polyline decoding / cumulative distance helpers."""

from __future__ import annotations

from dataclasses import dataclass

import polyline as _polyline_lib

from .distance import haversine_mi, meters_to_miles


@dataclass
class LatLon:
    lat: float
    lon: float


def decode_polyline(encoded: str, precision: int = 5) -> list[LatLon]:
    """Decode an encoded polyline into lat/lon points."""
    coords = _polyline_lib.decode(encoded, precision)
    return [LatLon(lat=lat, lon=lon) for lat, lon in coords]


def cumulative_distances_mi(points: list[LatLon]) -> list[float]:
    """Cumulative haversine distance along a polyline, starting at 0."""
    if not points:
        return []
    dists = [0.0]
    for i in range(1, len(points)):
        d = haversine_mi(points[i - 1].lat, points[i - 1].lon, points[i].lat, points[i].lon)
        dists.append(dists[-1] + d)
    return dists


def coords_from_lonlat_pairs(pairs: list[list[float]] | list[tuple[float, float]]) -> list[LatLon]:
    """Convert GeoJSON-style [lon, lat] pairs to LatLon list."""
    return [LatLon(lat=float(p[1]), lon=float(p[0])) for p in pairs]


def annotate_from_meters(
    distances_m: list[float], durations_s: list[float]
) -> tuple[list[float], list[float]]:
    """Convert OSRM annotation arrays (per-segment) into cumulative mi / s."""
    cum_mi = [0.0]
    cum_s = [0.0]
    for d_m, d_s in zip(distances_m, durations_s, strict=False):
        cum_mi.append(cum_mi[-1] + meters_to_miles(d_m))
        cum_s.append(cum_s[-1] + d_s)
    return cum_mi, cum_s
