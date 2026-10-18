"""Shared routing types."""

from __future__ import annotations

from dataclasses import dataclass, field

from apps.geo.polyline import LatLon


@dataclass
class RawRoute:
    """A route as returned by a routing provider, before weather/risk."""

    geometry: list[LatLon]
    distance_m: float
    duration_s: float
    # Cumulative distance (mi) and duration (s) aligned with geometry vertices.
    # If empty, callers fall back to haversine along geometry.
    cum_distance_mi: list[float] = field(default_factory=list)
    cum_duration_s: list[float] = field(default_factory=list)
    provider: str = ""
    summary: str = ""


@dataclass
class Checkpoint:
    index: int
    lat: float
    lon: float
    distance_mi: float
    eta_utc: str  # ISO 8601
    duration_from_start_s: float
