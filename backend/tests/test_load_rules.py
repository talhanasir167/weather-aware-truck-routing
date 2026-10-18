"""Load-rule grid tests."""

import pytest

from apps.risk.bands import RiskBand
from apps.risk.load_rules import load_escalation
from apps.risk.scoring import checkpoint_band


@pytest.mark.parametrize(
    "wind,load,expected",
    [
        (55, 0, RiskBand.NO_TRAVEL),
        (55, 10_000, RiskBand.NO_TRAVEL),
        (60, 50_000, RiskBand.NO_TRAVEL),
        (45, 30_000, RiskBand.LOW),  # exactly 30k does NOT escalate
        (45, 30_001, RiskBand.NO_TRAVEL),
        (54.9, 30_001, RiskBand.NO_TRAVEL),
        (44.9, 40_001, RiskBand.SEVERE),
        (35, 40_000, RiskBand.LOW),  # exactly 40k does NOT escalate
        (35, 40_001, RiskBand.SEVERE),
        (34.9, 50_000, RiskBand.LOW),  # below 35: no escalation
        (20, 80_000, RiskBand.LOW),
    ],
)
def test_load_escalation(wind, load, expected):
    assert load_escalation(wind, load) is expected


def test_escalation_never_downgrades():
    # Base is NO_TRAVEL from rain; load escalation is LOW — must stay NO_TRAVEL
    band = checkpoint_band(wind_mph=10, rain_in_hr=1.5, snow_in_hr=0, load_lb=10_000)
    assert band is RiskBand.NO_TRAVEL


def test_escalation_raises_base():
    # Wind HIGH (40 mph), load >40k → escalate to SEVERE
    band = checkpoint_band(wind_mph=40, rain_in_hr=0, snow_in_hr=0, load_lb=45_000)
    assert band is RiskBand.SEVERE
