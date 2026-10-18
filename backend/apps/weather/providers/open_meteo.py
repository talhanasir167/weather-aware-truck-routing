"""Open-Meteo hourly weather adapter (keyless, mph/inch units)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

from apps.core.http import client as http_client

logger = logging.getLogger(__name__)

HOURLY_FIELDS = "wind_speed_10m,wind_gusts_10m,rain,snowfall,precipitation,weather_code"


def _hour_bucket(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


@retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=0.5, max=4), reraise=True)
def fetch_hourly(
    locations: list[tuple[float, float]],
    forecast_days: int = 3,
) -> list[dict]:
    """Fetch hourly series for multiple (lat, lon) points in one request.

    Returns a list of Open-Meteo location payloads (same order as input).
    """
    if not locations:
        return []
    lats = ",".join(f"{lat:.4f}" for lat, _ in locations)
    lons = ",".join(f"{lon:.4f}" for _, lon in locations)
    params = {
        "latitude": lats,
        "longitude": lons,
        "hourly": HOURLY_FIELDS,
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": str(min(max(forecast_days, 1), 16)),
        "timezone": "UTC",
    }
    url = f"{settings.OPEN_METEO_BASE_URL}/v1/forecast"
    with http_client() as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    # Single location → object; multi → list
    if isinstance(data, list):
        return data
    return [data]


def sample_at_hour(payload: dict, hour_iso: str) -> dict | None:
    """Extract wind/rain/snow at the nearest hour from an Open-Meteo location payload."""
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        return None

    target = _hour_bucket(hour_iso).replace("Z", "")[:13]  # YYYY-MM-DDTHH
    # Open-Meteo times look like "2026-10-17T12:00"
    idx = None
    for i, t in enumerate(times):
        if t[:13] == target:
            idx = i
            break
    if idx is None:
        # try nearest
        try:
            target_dt = datetime.fromisoformat(hour_iso.replace("Z", "+00:00"))
            best_i, best_diff = 0, float("inf")
            for i, t in enumerate(times):
                dt = datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
                diff = abs((dt - target_dt).total_seconds())
                if diff < best_diff:
                    best_diff, best_i = diff, i
            # Only accept if within 90 minutes
            if best_diff <= 5400:
                idx = best_i
        except Exception:
            return None
    if idx is None:
        return None

    def _get(key: str, default: float = 0.0) -> float:
        arr = hourly.get(key) or []
        if idx >= len(arr) or arr[idx] is None:
            return default
        return float(arr[idx])

    codes = hourly.get("weather_code") or []
    code = codes[idx] if idx < len(codes) else None
    return {
        "wind_mph": _get("wind_speed_10m"),
        "wind_gusts_mph": _get("wind_gusts_10m"),
        "rain_in_hr": _get("rain"),
        "snow_in_hr": _get("snowfall"),
        "weather_code": int(code) if code is not None else None,
        "hour_utc": times[idx] + ("Z" if not times[idx].endswith("Z") else ""),
    }
