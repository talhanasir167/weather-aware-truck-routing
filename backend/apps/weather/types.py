from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WeatherSample:
    lat: float
    lon: float
    hour_utc: str  # ISO hour bucket
    wind_mph: float
    wind_gusts_mph: float
    rain_in_hr: float
    snow_in_hr: float
    weather_code: int | None = None
    available: bool = True
