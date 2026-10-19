"""End-to-end trip planning: route → sample → weather → risk → recommend → persist."""

from __future__ import annotations

from datetime import datetime, timezone

from django.conf import settings
from django.db import transaction

from apps.core.exceptions import AppError
from apps.geo.polyline import LatLon
from apps.geo.service import geocode
from apps.risk import (
    CheckpointRisk,
    RankableRoute,
    RiskBand,
    aggregate_route,
    band_reasons,
    checkpoint_band,
    midpoint_segment_miles,
    recommend,
)
from apps.routing.sampling import build_checkpoints
from apps.routing.service import get_route_alternatives
from apps.weather.demo_storm import apply_storm_to_samples
from apps.weather.service import fetch_for_checkpoints

from .models import Checkpoint as CheckpointModel
from .models import RoutePlan, Trip

VALID_INTERVALS = {10, 25, 50}


def _resolve_location(label_or_coords: str, lat: float | None, lon: float | None):
    if lat is not None and lon is not None:
        return label_or_coords or f"{lat:.5f}, {lon:.5f}", float(lat), float(lon)
    results = geocode(label_or_coords, limit=1)
    if not results:
        raise AppError(
            f"Could not resolve location: {label_or_coords}",
            code="geocode_failed",
            status_code=422,
        )
    r = results[0]
    return r.label, r.lat, r.lon


def _parse_departure(iso: str) -> datetime:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AppError(
            "departure must be timezone-aware ISO 8601",
            code="invalid_departure",
            status_code=400,
        ) from exc
    if dt.tzinfo is None:
        raise AppError(
            "departure must be timezone-aware ISO 8601",
            code="naive_departure",
            status_code=400,
        )
    return dt.astimezone(timezone.utc)


def plan_trip(
    *,
    origin: str,
    destination: str,
    departure: str,
    load_lb: int,
    interval_mi: int = 25,
    origin_lat: float | None = None,
    origin_lon: float | None = None,
    destination_lat: float | None = None,
    destination_lon: float | None = None,
    demo_storm: bool = False,
) -> Trip:
    if load_lb <= 0 or load_lb > 200_000:
        raise AppError("load_lb must be between 1 and 200000", code="invalid_load", status_code=400)
    if interval_mi not in VALID_INTERVALS:
        raise AppError(
            "interval_mi must be one of 10, 25, 50",
            code="invalid_interval",
            status_code=400,
        )

    dep = _parse_departure(departure)
    o_label, o_lat, o_lon = _resolve_location(origin, origin_lat, origin_lon)
    d_label, d_lat, d_lon = _resolve_location(destination, destination_lat, destination_lon)

    origin_ll = LatLon(lat=o_lat, lon=o_lon)
    dest_ll = LatLon(lat=d_lat, lon=d_lon)

    raw_routes, degraded = get_route_alternatives(origin_ll, dest_ll)
    if not raw_routes:
        raise AppError("No routes found between origin and destination", code="no_routes", status_code=422)

    # Cap trip length
    for rr in raw_routes:
        miles = rr.distance_m / 1609.344
        if miles > settings.MAX_TRIP_MILES:
            raise AppError(
                f"Trip exceeds max {settings.MAX_TRIP_MILES} miles",
                code="trip_too_long",
                status_code=422,
            )

    dep_iso = dep.isoformat().replace("+00:00", "Z")
    route_payloads = []
    all_wx_points: list[tuple[float, float, str]] = []
    route_cp_slices: list[tuple[int, int]] = []  # (start, end) into all_wx_points

    for rr in raw_routes:
        cps = build_checkpoints(
            rr.geometry,
            interval_mi,
            dep_iso,
            cum_distance_mi=rr.cum_distance_mi or None,
            cum_duration_s=rr.cum_duration_s or None,
        )
        if len(cps) > settings.MAX_CHECKPOINTS_PER_ROUTE:
            raise AppError(
                f"Too many checkpoints ({len(cps)}); increase interval_mi",
                code="too_many_checkpoints",
                status_code=422,
            )
        start = len(all_wx_points)
        for cp in cps:
            all_wx_points.append((cp.lat, cp.lon, cp.eta_utc))
        route_cp_slices.append((start, len(all_wx_points)))
        route_payloads.append({"raw": rr, "checkpoints": cps})

    weather_samples, wx_meta = fetch_for_checkpoints(all_wx_points)
    if wx_meta.get("unavailable"):
        degraded = [*degraded, "weather_partial"]

    rankables: list[RankableRoute] = []
    enriched = []

    for i, payload in enumerate(route_payloads):
        rr = payload["raw"]
        cps = payload["checkpoints"]
        start, end = route_cp_slices[i]
        wx_slice = weather_samples[start:end]
        if demo_storm:
            wx_slice = apply_storm_to_samples(wx_slice, route_index=i)

        distances = [cp.distance_mi for cp in cps]
        total_mi = rr.distance_m / 1609.344
        segments = midpoint_segment_miles(distances, total_mi)

        risk_cps: list[CheckpointRisk] = []
        cp_details = []
        for j, cp in enumerate(cps):
            wx = wx_slice[j]
            if wx.available:
                band = checkpoint_band(wx.wind_mph, wx.rain_in_hr, wx.snow_in_hr, load_lb)
                reasons = band_reasons(wx.wind_mph, wx.rain_in_hr, wx.snow_in_hr, load_lb)
                if demo_storm:
                    reasons = {**reasons, "demo_storm": True}
            else:
                band = RiskBand.LOW
                reasons = {"final_band": "Low", "drivers": ["forecast_unavailable"]}
            seg = segments[j] if j < len(segments) else 0.0
            risk_cps.append(CheckpointRisk(band=band, segment_miles=seg, index=j))
            cp_details.append(
                {
                    "checkpoint": cp,
                    "weather": wx,
                    "band": band,
                    "segment_miles": seg,
                    "reasons": reasons,
                }
            )

        metrics = aggregate_route(risk_cps)
        route_key = f"route_{i}"
        rankables.append(
            RankableRoute(route_id=route_key, metrics=metrics, duration_s=rr.duration_s)
        )
        enriched.append(
            {
                "route_key": route_key,
                "raw": rr,
                "metrics": metrics,
                "checkpoints": cp_details,
            }
        )

    rec = recommend(rankables)

    with transaction.atomic():
        trip = Trip.objects.create(
            origin_label=o_label,
            origin_lat=o_lat,
            origin_lon=o_lon,
            destination_label=d_label,
            destination_lat=d_lat,
            destination_lon=d_lon,
            departure_utc=dep,
            load_lb=load_lb,
            interval_mi=interval_mi,
            recommended_route_id=rec.route_id,
            recommendation_reasons=rec.reasons,
            degraded=degraded,
            meta={
                "weather": wx_meta,
                "ranking": rec.ranking,
                "demo_storm": demo_storm,
                "routing_provider": (
                    "ors"
                    if raw_routes and raw_routes[0].provider == "ors"
                    else ("osrm" if raw_routes else "none")
                ),
                "ors_configured": bool(settings.ORS_API_KEY),
            },
        )
        for rank, item in enumerate(enriched):
            rr = item["raw"]
            metrics = item["metrics"]
            geom = [[p.lon, p.lat] for p in rr.geometry]
            # Simplify geometry for storage if huge
            if len(geom) > 2000:
                step = max(1, len(geom) // 1500)
                geom = geom[::step]
                if geom[-1] != [rr.geometry[-1].lon, rr.geometry[-1].lat]:
                    geom.append([rr.geometry[-1].lon, rr.geometry[-1].lat])

            rp = RoutePlan.objects.create(
                trip=trip,
                route_key=item["route_key"],
                provider=rr.provider,
                distance_m=rr.distance_m,
                duration_s=rr.duration_s,
                geometry=geom,
                metrics={
                    "severe_miles": round(metrics.severe_miles, 2),
                    "high_miles": round(metrics.high_miles, 2),
                    "moderate_miles": round(metrics.moderate_miles, 2),
                    "low_miles": round(metrics.low_miles, 2),
                    "no_travel_miles": round(metrics.no_travel_miles, 2),
                    "avg_risk": round(metrics.avg_risk, 3),
                    "worst_band": metrics.worst_band.label,
                    "blocked": metrics.blocked,
                    "total_miles": round(metrics.total_miles, 2),
                    "band_miles": metrics.band_miles,
                },
                summary=rr.summary,
                is_recommended=(item["route_key"] == rec.route_id),
                rank=rec.ranking.index(item["route_key"]) if item["route_key"] in rec.ranking else rank,
            )
            # One round-trip per route instead of one per checkpoint.
            CheckpointModel.objects.bulk_create(
                [
                    CheckpointModel(
                        route=rp,
                        index=detail["checkpoint"].index,
                        lat=detail["checkpoint"].lat,
                        lon=detail["checkpoint"].lon,
                        distance_mi=detail["checkpoint"].distance_mi,
                        eta_utc=datetime.fromisoformat(
                            detail["checkpoint"].eta_utc.replace("Z", "+00:00")
                        ),
                        segment_miles=detail["segment_miles"],
                        band=detail["band"].label,
                        wind_mph=detail["weather"].wind_mph,
                        wind_gusts_mph=detail["weather"].wind_gusts_mph,
                        rain_in_hr=detail["weather"].rain_in_hr,
                        snow_in_hr=detail["weather"].snow_in_hr,
                        weather_available=detail["weather"].available,
                        reasons=detail["reasons"],
                    )
                    for detail in item["checkpoints"]
                ]
            )
    return trip


def trip_to_dict(trip: Trip) -> dict:
    routes = []
    for rp in trip.routes.prefetch_related("checkpoints").all():
        routes.append(
            {
                "id": rp.route_key,
                "provider": rp.provider,
                "distance_m": rp.distance_m,
                "distance_mi": round(rp.distance_m / 1609.344, 2),
                "duration_s": rp.duration_s,
                "duration_h": round(rp.duration_s / 3600, 2),
                "geometry": rp.geometry,
                "metrics": rp.metrics,
                "summary": rp.summary,
                "is_recommended": rp.is_recommended,
                "rank": rp.rank,
                "checkpoints": [
                    {
                        "index": c.index,
                        "lat": c.lat,
                        "lon": c.lon,
                        "distance_mi": c.distance_mi,
                        "eta_utc": c.eta_utc.isoformat().replace("+00:00", "Z"),
                        "segment_miles": round(c.segment_miles, 3),
                        "band": c.band,
                        "wind_mph": c.wind_mph,
                        "wind_gusts_mph": c.wind_gusts_mph,
                        "rain_in_hr": c.rain_in_hr,
                        "snow_in_hr": c.snow_in_hr,
                        "weather_available": c.weather_available,
                        "reasons": c.reasons,
                    }
                    for c in rp.checkpoints.all()
                ],
            }
        )
    return {
        "id": str(trip.id),
        "origin": {
            "label": trip.origin_label,
            "lat": trip.origin_lat,
            "lon": trip.origin_lon,
        },
        "destination": {
            "label": trip.destination_label,
            "lat": trip.destination_lat,
            "lon": trip.destination_lon,
        },
        "departure_utc": trip.departure_utc.isoformat().replace("+00:00", "Z"),
        "load_lb": trip.load_lb,
        "interval_mi": trip.interval_mi,
        "recommendation": {
            "route_id": trip.recommended_route_id,
            "reasons": trip.recommendation_reasons,
        },
        "degraded": trip.degraded,
        "meta": trip.meta,
        "routes": routes,
        "created_at": trip.created_at.isoformat().replace("+00:00", "Z"),
    }
