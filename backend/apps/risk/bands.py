"""Risk band enum. Ordered so max() works for combining metrics."""

from enum import IntEnum


class RiskBand(IntEnum):
    LOW = 0
    MODERATE = 1
    HIGH = 2
    SEVERE = 3
    NO_TRAVEL = 4

    @property
    def label(self) -> str:
        return {
            RiskBand.LOW: "Low",
            RiskBand.MODERATE: "Moderate",
            RiskBand.HIGH: "High",
            RiskBand.SEVERE: "Severe",
            RiskBand.NO_TRAVEL: "No Travel",
        }[self]
