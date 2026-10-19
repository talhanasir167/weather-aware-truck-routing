"""Routing service: guarantee up to 3 distinct route alternatives."""

from __future__ import annotations

import logging
import math

from apps.geo.distance import bearing_deg, offset_point
from apps.geo.polyline import LatLon
from apps.routing.dedupe import dedupe_routes
from apps.routing.providers import ors, osrm
from apps.routing.providers.ors import ORSAuthError, ORSRateLimitError
from apps.routing.types import RawRoute

logger = logging.getLogger(__name__)

TARGET_ROUTES = 3
VIA_OFFSETS_MI = (30.0, -30.0, 60.0, -60.0)


def _midpoint(origin: LatLon, destination: LatLon) -> LatLon:
    return LatLon(
        lat=(origin.lat + destination.lat) / 2.0,
        lon=(origin.lon + destination.lon) / 2.0,
    )


def _via_points(origin: LatLon, destination: LatLon) -> list[LatLon]:
    mid = _midpoint(origin, destination)
    br = bearing_deg(origin.lat, origin.lon, destination.lat, destination.lon)
    # Perpendicular bearings
    left = (br - 90) % 360
    right = (br + 90) % 360
    vias: list[LatLon] = []
    for offset in VIA_OFFSETS_MI:
        bearing = left if offset > 0 else right
        lat, lon = offset_point(mid.lat, mid.lon, bearing, abs(offset))
        vias.append(LatLon(lat=lat, lon=lon))
    return vias


def _fetch_primary(origin: LatLon, destination: LatLon) -> tuple[list[RawRoute], list[str]]:
    degraded: list[str] = []
    try:
        routes = ors.route(origin, destination, alternatives=TARGET_ROUTES)
        if routes:
            return routes, degraded
        degraded.append("ors_empty")
    except ORSAuthError:
        logger.info("ORS auth unavailable; using OSRM")
        degraded.append("ors_auth")
    except ORSRateLimitError:
        logger.warning("ORS rate limited; using OSRM")
        degraded.append("ors_rate_limit")
    except Exception:
        logger.exception("ORS failed; using OSRM")
        degraded.append("ors_error")

    routes = osrm.route(origin, destination, alternatives=TARGET_ROUTES)
    return routes, degraded


def _fetch_via(origin: LatLon, destination: LatLon, via: LatLon, use_ors: bool) -> list[RawRoute]:
    try:
        if use_ors:
            return ors.route(origin, destination, via=[via], alternatives=1)
    except Exception:
        logger.debug("ORS via failed", exc_info=True)
    try:
        return osrm.route(origin, destination, via=[via], alternatives=1)
    except Exception:
        logger.debug("OSRM via failed", exc_info=True)
        return []


def get_route_alternatives(
    origin: LatLon,
    destination: LatLon,
) -> tuple[list[RawRoute], list[str]]:
    """Return up to 3 distinct routes and a list of degradation flags."""
    candidates, degraded = _fetch_primary(origin, destination)
    use_ors = "ors_auth" not in degraded and "ors_rate_limit" not in degraded

    # Dedupe is the expensive step — run it once per added candidate, not twice.
    distinct = dedupe_routes(candidates)
    if len(distinct) < TARGET_ROUTES:
        for via in _via_points(origin, destination):
            extra = _fetch_via(origin, destination, via, use_ors=use_ors)
            if not extra:
                continue
            candidates.extend(extra)
            distinct = dedupe_routes(candidates)
            if len(distinct) >= TARGET_ROUTES:
                break

    kept = distinct[:TARGET_ROUTES]
    # Prefer shortest duration among remaining if we somehow have more
    kept = sorted(kept, key=lambda r: r.duration_s)[:TARGET_ROUTES]

    if len(kept) < TARGET_ROUTES:
        degraded.append("fewer_than_3_routes")

    # Drop empty geometries
    kept = [r for r in kept if r.geometry and not math.isclose(r.distance_m, 0)]
    return kept, degraded
