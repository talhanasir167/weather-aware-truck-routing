"""Load-weight escalation rules applied after base weather bands.

Rules (from assessment PDF):
- ≥55 mph → No Travel for any load
- 45–54 mph + >30,000 lb → No Travel
- 35–44 mph + >40,000 lb → Severe

Escalation never downgrades a higher base band.
"""

from .bands import RiskBand


def load_escalation(wind_mph: float, load_lb: float) -> RiskBand:
    """Return the escalation band implied by wind + load. LOW means no escalation."""
    if wind_mph >= 55:
        return RiskBand.NO_TRAVEL
    if 45 <= wind_mph < 55 and load_lb > 30_000:
        return RiskBand.NO_TRAVEL
    if 35 <= wind_mph < 45 and load_lb > 40_000:
        return RiskBand.SEVERE
    return RiskBand.LOW
