"""Per-checkpoint risk scoring."""

from .bands import RiskBand
from .load_rules import load_escalation
from .thresholds import rain_band, snow_band, wind_band


def base_band(wind_mph: float, rain_in_hr: float, snow_in_hr: float) -> RiskBand:
    """Checkpoint base band = max(wind, rain, snow)."""
    return max(wind_band(wind_mph), rain_band(rain_in_hr), snow_band(snow_in_hr))


def checkpoint_band(
    wind_mph: float,
    rain_in_hr: float,
    snow_in_hr: float,
    load_lb: float,
) -> RiskBand:
    """Final checkpoint band after load escalation."""
    base = base_band(wind_mph, rain_in_hr, snow_in_hr)
    escalation = load_escalation(wind_mph, load_lb)
    return max(base, escalation)


def band_reasons(
    wind_mph: float,
    rain_in_hr: float,
    snow_in_hr: float,
    load_lb: float,
) -> dict:
    """Explain which metric drove the band (useful for UI/Loom)."""
    w = wind_band(wind_mph)
    r = rain_band(rain_in_hr)
    s = snow_band(snow_in_hr)
    base = max(w, r, s)
    esc = load_escalation(wind_mph, load_lb)
    final = max(base, esc)
    drivers = []
    if w == final:
        drivers.append(f"wind={wind_mph:.1f}mph→{w.label}")
    if r == final:
        drivers.append(f"rain={rain_in_hr:.3f}in/hr→{r.label}")
    if s == final:
        drivers.append(f"snow={snow_in_hr:.2f}in/hr→{s.label}")
    if esc == final and esc > base:
        drivers.append(f"load_escalation({load_lb:.0f}lb)→{esc.label}")
    return {
        "wind_band": w.label,
        "rain_band": r.label,
        "snow_band": s.label,
        "base_band": base.label,
        "load_escalation": esc.label,
        "final_band": final.label,
        "drivers": drivers,
    }
