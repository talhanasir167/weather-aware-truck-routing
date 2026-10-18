"""Haversine and polyline distance helpers. Pure math — no I/O."""

from __future__ import annotations

import math

EARTH_RADIUS_MI = 3958.7613
METERS_PER_MILE = 1609.344


def haversine_mi(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles between two WGS84 points."""
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    dlat = rlat2 - rlat1
    dlon = rlon2 - rlon1
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_MI * math.asin(math.sqrt(a))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Initial bearing from point 1 to point 2 in degrees [0, 360)."""
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(rlat2)
    y = math.cos(rlat1) * math.sin(rlat2) - math.sin(rlat1) * math.cos(rlat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def offset_point(
    lat: float, lon: float, bearing_degrees: float, distance_mi: float
) -> tuple[float, float]:
    """Move from (lat, lon) along bearing by distance_mi. Returns (lat, lon)."""
    br = math.radians(bearing_degrees)
    rlat = math.radians(lat)
    rlon = math.radians(lon)
    ang = distance_mi / EARTH_RADIUS_MI
    lat2 = math.asin(
        math.sin(rlat) * math.cos(ang) + math.cos(rlat) * math.sin(ang) * math.cos(br)
    )
    lon2 = rlon + math.atan2(
        math.sin(br) * math.sin(ang) * math.cos(rlat),
        math.cos(ang) - math.sin(rlat) * math.sin(lat2),
    )
    return math.degrees(lat2), ((math.degrees(lon2) + 540) % 360) - 180


def meters_to_miles(m: float) -> float:
    return m / METERS_PER_MILE
