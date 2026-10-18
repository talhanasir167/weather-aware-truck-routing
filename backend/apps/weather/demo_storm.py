"""Synthetic Midwest storm overlay for Loom / calm-weather demos.

Injects elevated wind/rain/snow on a band of checkpoints so risk bands,
severe/high miles, and recommendation differences are visible even when
the live forecast is quiet. Deterministic per route index.
"""

from __future__ import annotations

from apps.weather.types import WeatherSample

# Per-route storm intensity (route_0 mildest diversion, route_2 harshest core).
# Values chosen to hit Moderate / High / Severe thresholds from the PDF.
_ROUTE_PROFILES = (
    # route_0 — mostly Moderate wind, light rain (should often win)
    {"wind": 28.0, "rain": 0.12, "snow": 0.0, "core_wind": 36.0, "core_rain": 0.28},
    # route_1 — High wind + Moderate rain
    {"wind": 38.0, "rain": 0.18, "snow": 0.0, "core_wind": 48.0, "core_rain": 0.35},
    # route_2 — Severe wind band + heavy rain (often loses)
    {"wind": 46.0, "rain": 0.40, "snow": 0.6, "core_wind": 52.0, "core_rain": 0.65},
)


def apply_storm_to_samples(
    samples: list[WeatherSample],
    *,
    route_index: int,
) -> list[WeatherSample]:
    """Overlay storm weather onto a route's checkpoint samples (in place copy)."""
    if not samples:
        return samples
    profile = _ROUTE_PROFILES[min(route_index, len(_ROUTE_PROFILES) - 1)]
    n = len(samples)
    # Storm hits the middle ~45% of the route
    start = max(0, int(n * 0.30))
    end = min(n, int(n * 0.75))
    core_start = max(start, int(n * 0.45))
    core_end = min(end, int(n * 0.60))

    out: list[WeatherSample] = []
    for i, wx in enumerate(samples):
        if start <= i < end:
            in_core = core_start <= i < core_end
            wind = profile["core_wind"] if in_core else profile["wind"]
            rain = profile["core_rain"] if in_core else profile["rain"]
            snow = profile["snow"] if in_core else 0.0
            out.append(
                WeatherSample(
                    lat=wx.lat,
                    lon=wx.lon,
                    hour_utc=wx.hour_utc,
                    wind_mph=max(wx.wind_mph, wind),
                    wind_gusts_mph=max(wx.wind_gusts_mph, wind + 8),
                    rain_in_hr=max(wx.rain_in_hr, rain),
                    snow_in_hr=max(wx.snow_in_hr, snow),
                    weather_code=wx.weather_code,
                    available=True,
                )
            )
        else:
            out.append(wx)
    return out


def boost_heatmap_frame(
    risk_row: list[float],
    wind_row: list[float],
    rain_row: list[float],
    snow_row: list[float],
    hour_index: int,
) -> None:
    """Mutate one heatmap hour in-place with a moving storm band (Loom-visible)."""
    n = len(risk_row)
    if n == 0:
        return
    # Storm drifts along the corridor over 0–48h
    center = int((hour_index / 48.0) * (n - 1))
    half = max(2, n // 8)
    for i in range(n):
        dist = abs(i - center)
        if dist > half:
            continue
        intensity = 1.0 - dist / half
        wind_row[i] = max(wind_row[i], 30.0 + intensity * 22.0)
        rain_row[i] = max(rain_row[i], 0.10 + intensity * 0.45)
        # risk score 0–4
        if intensity > 0.75:
            risk_row[i] = max(risk_row[i], 3.0)  # Severe
        elif intensity > 0.4:
            risk_row[i] = max(risk_row[i], 2.0)  # High
        else:
            risk_row[i] = max(risk_row[i], 1.0)  # Moderate
