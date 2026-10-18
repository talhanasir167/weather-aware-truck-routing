"""49-frame heatmap builder for the 0–48h forecast slider."""

from __future__ import annotations

from datetime import timedelta, timezone

from django.conf import settings

from apps.geo.polyline import LatLon
from apps.heatmap.corridor import build_corridor_grid
from apps.planner.models import Trip
from apps.risk.scoring import checkpoint_band
from apps.weather.demo_storm import boost_heatmap_frame
from apps.weather.service import fetch_for_checkpoints


def build_heatmap(trip: Trip) -> dict:
    """Return corridor grid + 49 hourly frames of risk/wind/rain/snow."""
    routes = list(trip.routes.all())
    geoms: list[list[LatLon]] = []
    for rp in routes:
        geoms.append([LatLon(lat=p[1], lon=p[0]) for p in rp.geometry])

    grid = build_corridor_grid(
        geoms,
        spacing_mi=20.0,
        lateral_offsets_mi=(-25.0, 0.0, 25.0),
        max_points=settings.HEATMAP_MAX_POINTS,
    )

    dep = trip.departure_utc.astimezone(timezone.utc)
    hours = [
        (dep + timedelta(hours=h)).replace(minute=0, second=0, microsecond=0)
        for h in range(49)
    ]
    hour_isos = [h.isoformat().replace("+00:00", "Z") for h in hours]

    # Fetch weather for every (point, hour) — dedupe/cache inside weather service
    points: list[tuple[float, float, str]] = []
    for h_iso in hour_isos:
        for pt in grid:
            points.append((pt.lat, pt.lon, h_iso))

    samples, meta = fetch_for_checkpoints(points)

    n_points = len(grid)
    n_hours = 49
    risk = [[0.0] * n_points for _ in range(n_hours)]
    wind = [[0.0] * n_points for _ in range(n_hours)]
    rain = [[0.0] * n_points for _ in range(n_hours)]
    snow = [[0.0] * n_points for _ in range(n_hours)]

    for hi in range(n_hours):
        for pi in range(n_points):
            idx = hi * n_points + pi
            wx = samples[idx]
            if wx.available:
                band = checkpoint_band(wx.wind_mph, wx.rain_in_hr, wx.snow_in_hr, trip.load_lb)
                risk[hi][pi] = float(int(band))
                wind[hi][pi] = wx.wind_mph
                rain[hi][pi] = wx.rain_in_hr
                snow[hi][pi] = wx.snow_in_hr

    demo_storm = bool((trip.meta or {}).get("demo_storm"))
    if demo_storm:
        for hi in range(n_hours):
            boost_heatmap_frame(risk[hi], wind[hi], rain[hi], snow[hi], hi)
        meta = {**(meta or {}), "demo_storm": True}

    return {
        "trip_id": str(trip.id),
        "grid_points": [{"lat": p.lat, "lon": p.lon} for p in grid],
        "hours": hour_isos,
        "frames": {
            "risk": risk,
            "wind": wind,
            "rain": rain,
            "snow": snow,
        },
        "meta": meta,
    }
