"""Route-level aggregation of checkpoint risk into mileage metrics."""

from dataclasses import dataclass, field

from .bands import RiskBand


@dataclass
class CheckpointRisk:
    """A checkpoint with an assigned band and the miles it owns."""

    band: RiskBand
    segment_miles: float
    # Optional metadata for callers; not used in aggregation math.
    index: int = 0


@dataclass
class RouteMetrics:
    severe_miles: float = 0.0
    high_miles: float = 0.0
    moderate_miles: float = 0.0
    low_miles: float = 0.0
    no_travel_miles: float = 0.0
    avg_risk: float = 0.0
    worst_band: RiskBand = RiskBand.LOW
    blocked: bool = False
    total_miles: float = 0.0
    checkpoint_count: int = 0
    band_miles: dict = field(default_factory=dict)


def midpoint_segment_miles(distances_from_start: list[float], total_miles: float) -> list[float]:
    """Attribute miles to each checkpoint via midpoint splits.

    Each checkpoint owns the segment from midpoint(prev, cur) to midpoint(cur, next).
    First and last also own their end stubs. Segment miles sum to exactly total_miles.
    """
    n = len(distances_from_start)
    if n == 0:
        return []
    if n == 1:
        return [total_miles]

    mids: list[float] = []
    for i in range(n - 1):
        mids.append(0.5 * (distances_from_start[i] + distances_from_start[i + 1]))

    segments: list[float] = []
    # First owns [0, mid0]
    segments.append(mids[0] - 0.0)
    for i in range(1, n - 1):
        segments.append(mids[i] - mids[i - 1])
    # Last owns [mid_{n-2}, total]
    segments.append(total_miles - mids[-1])

    # Correct floating-point drift so sum == total_miles
    drift = total_miles - sum(segments)
    segments[-1] += drift
    return segments


def aggregate_route(checkpoints: list[CheckpointRisk]) -> RouteMetrics:
    """Compute per-route metrics from checkpoint bands + segment miles."""
    m = RouteMetrics()
    if not checkpoints:
        return m

    total = 0.0
    weighted = 0.0
    worst = RiskBand.LOW

    for cp in checkpoints:
        miles = max(0.0, cp.segment_miles)
        total += miles
        weighted += int(cp.band) * miles
        if cp.band > worst:
            worst = cp.band

        if cp.band == RiskBand.NO_TRAVEL:
            m.no_travel_miles += miles
        elif cp.band == RiskBand.SEVERE:
            m.severe_miles += miles
        elif cp.band == RiskBand.HIGH:
            m.high_miles += miles
        elif cp.band == RiskBand.MODERATE:
            m.moderate_miles += miles
        else:
            m.low_miles += miles

    m.total_miles = total
    m.avg_risk = (weighted / total) if total > 0 else 0.0
    m.worst_band = worst
    m.blocked = m.no_travel_miles > 0
    m.checkpoint_count = len(checkpoints)
    m.band_miles = {
        "low": round(m.low_miles, 3),
        "moderate": round(m.moderate_miles, 3),
        "high": round(m.high_miles, 3),
        "severe": round(m.severe_miles, 3),
        "no_travel": round(m.no_travel_miles, 3),
    }
    return m
