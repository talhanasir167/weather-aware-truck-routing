from apps.risk.bands import RiskBand
from apps.risk.scoring import base_band, checkpoint_band


def test_max_across_metrics():
    assert base_band(10, 0, 2.5) is RiskBand.SEVERE  # snow Severe
    assert base_band(40, 0, 0) is RiskBand.HIGH  # wind High
    assert base_band(10, 0.05, 0.1) is RiskBand.LOW


def test_all_low():
    assert checkpoint_band(10, 0.05, 0.1, 20_000) is RiskBand.LOW
