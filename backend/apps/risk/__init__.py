"""Pure risk engine — no Django, no network, no clock.

Public surface for the rest of the backend.
"""

from .aggregate import CheckpointRisk, RouteMetrics, aggregate_route, midpoint_segment_miles
from .bands import RiskBand
from .recommend import RankableRoute, Recommendation, recommend
from .scoring import band_reasons, base_band, checkpoint_band

__all__ = [
    "RiskBand",
    "base_band",
    "checkpoint_band",
    "band_reasons",
    "CheckpointRisk",
    "RouteMetrics",
    "aggregate_route",
    "midpoint_segment_miles",
    "RankableRoute",
    "Recommendation",
    "recommend",
]
