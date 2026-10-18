"""OSRM routing adapter (public demo or self-hosted)."""

from __future__ import annotations

import logging

from django.conf import settings

from apps.core.http import client as http_client
from apps.geo.polyline import LatLon, annotate_from_meters, decode_polyline
from apps.routing.types import RawRoute

logger = logging.getLogger(__name__)


def _coords_param(points: list[tuple[float, float]]) -> str:
    """points are (lon, lat)."""
    return ";".join(f"{lon},{lat}" for lon, lat in points)


def route(
    origin: LatLon,
    destination: LatLon,
    via: list[LatLon] | None = None,
    alternatives: int = 3,
) -> list[RawRoute]:
    """Request driving routes from OSRM."""
    pts: list[tuple[float, float]] = [(origin.lon, origin.lat)]
    for v in via or []:
        pts.append((v.lon, v.lat))
    pts.append((destination.lon, destination.lat))

    url = f"{settings.OSRM_BASE_URL}/route/v1/driving/{_coords_param(pts)}"
    params = {
        "alternatives": str(min(alternatives, 3)),
        "overview": "full",
        "geometries": "polyline",
        "steps": "false",
        "annotations": "distance,duration",
    }
    with http_client() as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != "Ok":
        logger.warning("OSRM non-Ok: %s", data.get("code"))
        return []

    routes: list[RawRoute] = []
    for r in data.get("routes", []):
        geom = decode_polyline(r["geometry"])
        cum_mi: list[float] = []
        cum_s: list[float] = []
        legs = r.get("legs", [])
        if legs:
            ann = legs[0].get("annotation") or {}
            dist_arr = ann.get("distance") or []
            dur_arr = ann.get("duration") or []
            if dist_arr and dur_arr and len(dist_arr) == len(dur_arr):
                # annotations are per-edge; geometry has n+1 vertices for one leg
                # For multi-leg we concatenate.
                all_d: list[float] = []
                all_u: list[float] = []
                for leg in legs:
                    a = leg.get("annotation") or {}
                    all_d.extend(a.get("distance") or [])
                    all_u.extend(a.get("duration") or [])
                if all_d and all_u:
                    cum_mi, cum_s = annotate_from_meters(all_d, all_u)

        routes.append(
            RawRoute(
                geometry=geom,
                distance_m=float(r["distance"]),
                duration_s=float(r["duration"]),
                cum_distance_mi=cum_mi,
                cum_duration_s=cum_s,
                provider="osrm",
                summary=f"OSRM {r['distance'] / 1609.344:.1f} mi",
            )
        )
    return routes
