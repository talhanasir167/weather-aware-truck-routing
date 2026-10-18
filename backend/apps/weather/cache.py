"""Redis/locmem weather cache keyed by grid + hour."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from django.core.cache import cache


def grid_key(lat: float, lon: float, hour_iso: str) -> str:
    dt = datetime.fromisoformat(hour_iso.replace("Z", "+00:00")).astimezone(timezone.utc)
    hour = dt.replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H")
    return f"wx:v1:{lat:.2f}:{lon:.2f}:{hour}"


def snap_grid(lat: float, lon: float) -> tuple[float, float]:
    """Snap to ~0.1° grid (≈7 mi)."""
    return round(lat, 1), round(lon, 1)


def get_many(keys: list[str]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for k in keys:
        val = cache.get(k)
        if val is not None:
            if isinstance(val, str):
                val = json.loads(val)
            out[k] = val
    return out


def set_many(items: dict[str, dict], ttl_near: int = 3600, ttl_far: int = 21600) -> None:
    """Cache weather samples. Near-term (next 24h) uses shorter TTL."""
    now = datetime.now(timezone.utc)
    for k, v in items.items():
        # Parse hour from key ...:YYYY-MM-DDTHH
        try:
            hour_part = k.rsplit(":", 1)[-1]
            hour_dt = datetime.strptime(hour_part, "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
            ttl = ttl_near if (hour_dt - now).total_seconds() <= 86400 else ttl_far
        except Exception:
            ttl = ttl_near
        cache.set(k, v, ttl)
