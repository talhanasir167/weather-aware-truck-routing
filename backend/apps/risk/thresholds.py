"""Weather threshold classification per assessment PDF.

Band boundaries in the PDF share endpoints (e.g. rain 0.25 is listed as both
Moderate and High). Resolution: lower bound inclusive, upper exclusive,
evaluated highest-band-first. Wind No Travel uses >=55; rain/snow use strict >.
"""

from .bands import RiskBand


def wind_band(mph: float) -> RiskBand:
    """Classify sustained wind speed in mph.

    PDF: <25 Low | 25–34 Moderate | 35–44 High | 45–54 Severe | ≥55 No Travel
    """
    if mph >= 55:
        return RiskBand.NO_TRAVEL
    if mph >= 45:
        return RiskBand.SEVERE
    if mph >= 35:
        return RiskBand.HIGH
    if mph >= 25:
        return RiskBand.MODERATE
    return RiskBand.LOW


def rain_band(in_hr: float) -> RiskBand:
    """Classify rain rate in inches per hour.

    PDF: <0.10 Low | 0.10–0.25 Moderate | 0.25–0.50 High | 0.50–1.00 Severe | >1.00 No Travel
    Exactly 1.00 is Severe (strict '>' for No Travel).
    """
    if in_hr > 1.00:
        return RiskBand.NO_TRAVEL
    if in_hr >= 0.50:
        return RiskBand.SEVERE
    if in_hr >= 0.25:
        return RiskBand.HIGH
    if in_hr >= 0.10:
        return RiskBand.MODERATE
    return RiskBand.LOW


def snow_band(in_hr: float) -> RiskBand:
    """Classify snowfall rate in inches per hour.

    PDF: <0.5 Low | 0.5–1.0 Moderate | 1.0–2.0 High | 2.0–3.0 Severe | >3.0 No Travel
    Exactly 3.0 is Severe (strict '>' for No Travel).
    """
    if in_hr > 3.0:
        return RiskBand.NO_TRAVEL
    if in_hr >= 2.0:
        return RiskBand.SEVERE
    if in_hr >= 1.0:
        return RiskBand.HIGH
    if in_hr >= 0.5:
        return RiskBand.MODERATE
    return RiskBand.LOW
