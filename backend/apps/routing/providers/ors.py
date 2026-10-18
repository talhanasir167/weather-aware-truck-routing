"""OpenRouteService driving-hgv adapter."""

from __future__ import annotations

import logging

from django.conf import settings

from apps.core.http import client as http_client
from apps.geo.polyline import LatLon, coords_from_lonlat_pairs, cumulative_distances_mi
from apps.routing.types import RawRoute

logger = logging.getLogger(__name__)


class ORSAuthError(Exception):
    pass


class ORSRateLimitError(Exception):
    pass


def route(
    origin: LatLon,
    destination: LatLon,
    via: list[LatLon] | None = None,
    alternatives: int = 3,
) -> list[RawRoute]:
    """Request HGV routes from ORS with alternative_routes when possible."""
    api_key = settings.ORS_API_KEY
    if not api_key:
        raise ORSAuthError("ORS_API_KEY not configured")

    coords = [[origin.lon, origin.lat]]
    for v in via or []:
        coords.append([v.lon, v.lat])
    coords.append([destination.lon, destination.lat])

    body: dict = {
        "coordinates": coords,
        "instructions": False,
        "geometry": True,
        "elevation": False,
    }
    # alternative_routes only works without via points
    if not via and alternatives > 1:
        body["alternative_routes"] = {
            "target_count": min(alternatives, 3),
            "share_factor": 0.6,
            "weight_factor": 1.6,
        }

    url = f"{settings.ORS_BASE_URL}/v2/directions/driving-hgv/geojson"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }
    with http_client() as client:
        resp = client.post(url, json=body, headers=headers)
        if resp.status_code in (401, 403):
            raise ORSAuthError(f"ORS auth failed: {resp.status_code}")
        if resp.status_code == 429:
            raise ORSRateLimitError("ORS rate limited")
        resp.raise_for_status()
        data = resp.json()

    routes: list[RawRoute] = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        summary = props.get("summary") or {}
        coords_ll = feat.get("geometry", {}).get("coordinates") or []
        geom = coords_from_lonlat_pairs(coords_ll)
        cum_mi = cumulative_distances_mi(geom)
        # Uniform duration along geometry (ORS GeoJSON summary has total duration)
        total_dur = float(summary.get("duration") or props.get("duration") or 0)
        total_dist = float(summary.get("distance") or props.get("distance") or 0)
        cum_s = []
        if cum_mi and cum_mi[-1] > 0 and total_dur > 0:
            cum_s = [d / cum_mi[-1] * total_dur for d in cum_mi]
        routes.append(
            RawRoute(
                geometry=geom,
                distance_m=total_dist,
                duration_s=total_dur,
                cum_distance_mi=cum_mi,
                cum_duration_s=cum_s,
                provider="ors",
                summary=f"ORS HGV {total_dist / 1609.344:.1f} mi",
            )
        )
    return routes
