"""Weather service: grid dedupe, cache, batched Open-Meteo fetch."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

from apps.weather import cache as wx_cache
from apps.weather.providers import open_meteo
from apps.weather.types import WeatherSample

logger = logging.getLogger(__name__)

# Smaller batches are more resilient when Open-Meteo returns intermittent 503s.
BATCH_SIZE = 5


def _forecast_days_needed(hours: list[str]) -> int:
    if not hours:
        return 3
    now = datetime.now(timezone.utc)
    max_h = max(
        datetime.fromisoformat(h.replace("Z", "+00:00")).astimezone(timezone.utc) for h in hours
    )
    days = max(1, int((max_h - now).total_seconds() // 86400) + 2)
    return min(days, 16)


def fetch_for_checkpoints(
    points: list[tuple[float, float, str]],
) -> tuple[list[WeatherSample], dict]:
    """Fetch weather for (lat, lon, eta_iso) points.

    Returns (samples aligned with input order, meta dict with cache stats).
    """
    if not points:
        return [], {"cache_hit_ratio": 1.0, "fetched": 0, "requested": 0}

    # Build unique grid+hour keys
    key_for_idx: list[str] = []
    grid_for_key: dict[str, tuple[float, float, str]] = {}
    for lat, lon, eta in points:
        glat, glon = wx_cache.snap_grid(lat, lon)
        key = wx_cache.grid_key(glat, glon, eta)
        key_for_idx.append(key)
        grid_for_key[key] = (glat, glon, eta)

    unique_keys = list(grid_for_key.keys())
    cached = wx_cache.get_many(unique_keys)
    misses = [k for k in unique_keys if k not in cached]

    # Group misses by unique grid point (fetch full hourly series once per point)
    points_to_fetch: dict[tuple[float, float], list[str]] = defaultdict(list)
    for k in misses:
        glat, glon, eta = grid_for_key[k]
        points_to_fetch[(glat, glon)].append(eta)

    fetched_payloads: dict[tuple[float, float], dict] = {}
    all_hours = [grid_for_key[k][2] for k in misses]
    forecast_days = _forecast_days_needed(all_hours or [p[2] for p in points])

    locs = list(points_to_fetch.keys())
    fetch_errors = 0
    for i in range(0, len(locs), BATCH_SIZE):
        batch = locs[i : i + BATCH_SIZE]
        try:
            payloads = open_meteo.fetch_hourly(batch, forecast_days=forecast_days)
            for loc, payload in zip(batch, payloads, strict=False):
                if payload:
                    fetched_payloads[loc] = payload
                else:
                    fetch_errors += 1
        except Exception:
            fetch_errors += len(batch)
            logger.exception("Open-Meteo batch failed; continuing with cache/unavailable")

    # Populate cache from fetched payloads
    to_cache: dict[str, dict] = {}
    for k in misses:
        glat, glon, eta = grid_for_key[k]
        payload = fetched_payloads.get((glat, glon))
        if not payload:
            continue
        sample = open_meteo.sample_at_hour(payload, eta)
        if sample:
            to_cache[k] = sample
    if to_cache:
        wx_cache.set_many(to_cache)
        cached.update(to_cache)

    samples: list[WeatherSample] = []
    for (lat, lon, eta), key in zip(points, key_for_idx, strict=True):
        data = cached.get(key)
        if data:
            samples.append(
                WeatherSample(
                    lat=lat,
                    lon=lon,
                    hour_utc=data.get("hour_utc", eta),
                    wind_mph=float(data.get("wind_mph", 0)),
                    wind_gusts_mph=float(data.get("wind_gusts_mph", 0)),
                    rain_in_hr=float(data.get("rain_in_hr", 0)),
                    snow_in_hr=float(data.get("snow_in_hr", 0)),
                    weather_code=data.get("weather_code"),
                    available=True,
                )
            )
        else:
            samples.append(
                WeatherSample(
                    lat=lat,
                    lon=lon,
                    hour_utc=eta,
                    wind_mph=0,
                    wind_gusts_mph=0,
                    rain_in_hr=0,
                    snow_in_hr=0,
                    available=False,
                )
            )

    hits = len(unique_keys) - len(misses)
    available_n = sum(1 for s in samples if s.available)
    meta = {
        "cache_hit_ratio": (hits / len(unique_keys)) if unique_keys else 1.0,
        "fetched": len(to_cache),
        "requested": len(unique_keys),
        "unique_grid_points": len(locs)
        if locs
        else len({wx_cache.snap_grid(p[0], p[1]) for p in points}),
        "available": available_n,
        "unavailable": len(samples) - available_n,
        "fetch_errors": fetch_errors,
    }
    return samples, meta
