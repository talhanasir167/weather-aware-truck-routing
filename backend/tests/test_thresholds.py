"""Exhaustive band-boundary tests pinning §5.1 inclusivity decisions."""

import pytest

from apps.risk.bands import RiskBand
from apps.risk.thresholds import rain_band, snow_band, wind_band


@pytest.mark.parametrize(
    "mph,expected",
    [
        (0.0, RiskBand.LOW),
        (24.9, RiskBand.LOW),
        (25.0, RiskBand.MODERATE),
        (34.9, RiskBand.MODERATE),
        (35.0, RiskBand.HIGH),
        (44.9, RiskBand.HIGH),
        (45.0, RiskBand.SEVERE),
        (54.0, RiskBand.SEVERE),
        (54.9, RiskBand.SEVERE),
        (55.0, RiskBand.NO_TRAVEL),
        (80.0, RiskBand.NO_TRAVEL),
    ],
)
def test_wind_band(mph, expected):
    assert wind_band(mph) is expected


@pytest.mark.parametrize(
    "in_hr,expected",
    [
        (0.0, RiskBand.LOW),
        (0.099, RiskBand.LOW),
        (0.10, RiskBand.MODERATE),
        (0.249, RiskBand.MODERATE),
        (0.25, RiskBand.HIGH),
        (0.499, RiskBand.HIGH),
        (0.50, RiskBand.SEVERE),
        (0.999, RiskBand.SEVERE),
        (1.00, RiskBand.SEVERE),  # strict '>' for No Travel
        (1.001, RiskBand.NO_TRAVEL),
    ],
)
def test_rain_band(in_hr, expected):
    assert rain_band(in_hr) is expected


@pytest.mark.parametrize(
    "in_hr,expected",
    [
        (0.0, RiskBand.LOW),
        (0.49, RiskBand.LOW),
        (0.5, RiskBand.MODERATE),
        (0.99, RiskBand.MODERATE),
        (1.0, RiskBand.HIGH),
        (1.99, RiskBand.HIGH),
        (2.0, RiskBand.SEVERE),
        (2.99, RiskBand.SEVERE),
        (3.0, RiskBand.SEVERE),  # strict '>' for No Travel
        (3.01, RiskBand.NO_TRAVEL),
    ],
)
def test_snow_band(in_hr, expected):
    assert snow_band(in_hr) is expected
