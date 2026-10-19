"""Open-Meteo hourly weather adapter (keyless, mph/inch units)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from django.conf import settings
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from apps.core.http import client as http_client

logger = logging.getLogger(__name__)

HOURLY_FIELDS = "wind_speed_10m,wind_gusts_10m,rain,snowfall,precipitation,weather_code"


class OpenMeteoTransientError(Exception):
    """503 / timeout — safe to retry."""


def _hour_bucket(iso: str) -> str:
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    return dt.replace(minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def _request_hourly(
    locations: list[tuple[float, float]],
    forecast_days: int,
) -> list[dict]:
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
        try:
            resp = client.get(url, params=params)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise OpenMeteoTransientError(str(exc)) from exc
        if resp.status_code in (429, 500, 502, 503, 504):
            raise OpenMeteoTransientError(f"Open-Meteo HTTP {resp.status_code}")
        resp.raise_for_status()
        data = resp.json()

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and data.get("error"):
        raise RuntimeError(data.get("reason") or "Open-Meteo error")
    return [data]


@retry(
    retry=retry_if_exception_type(OpenMeteoTransientError),
    stop=stop_after_attempt(4),
    wait=wait_exponential_jitter(initial=0.4, max=5),
    reraise=True,
)
def _fetch_batch(
    locations: list[tuple[float, float]],
    forecast_days: int,
) -> list[dict]:
    return _request_hourly(locations, forecast_days)


def fetch_hourly(
    locations: list[tuple[float, float]],
    forecast_days: int = 3,
) -> list[dict]:
    """Fetch hourly series for multiple (lat, lon) points.

    Tries a batch request first; on failure falls back to one location at a time
    so a single flaky point does not wipe the whole corridor.
    """
    if not locations:
        return []
    try:
        return _fetch_batch(locations, forecast_days)
    except Exception:
        logger.warning(
            "Open-Meteo batch failed (%d pts); falling back to per-point",
            len(locations),
            exc_info=True,
        )

    out: list[dict] = []
    for loc in locations:
        try:
            payloads = _fetch_batch([loc], forecast_days)
            out.append(payloads[0] if payloads else {})
        except Exception:
            logger.warning("Open-Meteo point failed %s", loc, exc_info=True)
            out.append({})
    return out


def sample_at_hour(payload: dict, hour_iso: str) -> dict | None:
    """Extract wind/rain/snow at the nearest hour from an Open-Meteo location payload."""
    if not payload:
        return None
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        return None

    target = _hour_bucket(hour_iso).replace("Z", "")[:13]  # YYYY-MM-DDTHH
    idx = None
    for i, t in enumerate(times):
        if t[:13] == target:
            idx = i
            break
    if idx is None:
        try:
            target_dt = datetime.fromisoformat(hour_iso.replace("Z", "+00:00"))
            best_i, best_diff = 0, float("inf")
            for i, t in enumerate(times):
                dt = datetime.fromisoformat(t).replace(tzinfo=timezone.utc)
                diff = abs((dt - target_dt).total_seconds())
                if diff < best_diff:
                    best_diff, best_i = diff, i
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
