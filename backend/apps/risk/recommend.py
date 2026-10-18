"""Route recommendation cascade per assessment PDF.

Prefer:
1. Fewest Severe miles
2. Fewest High miles
3. Lowest average risk
4. Shortest travel times

Addition: routes with No Travel miles are flagged blocked and sorted last.
"""

from dataclasses import dataclass, field

from .aggregate import RouteMetrics
from .bands import RiskBand


@dataclass
class RankableRoute:
    route_id: str
    metrics: RouteMetrics
    duration_s: float


@dataclass
class Recommendation:
    route_id: str
    reasons: list[str] = field(default_factory=list)
    ranking: list[str] = field(default_factory=list)


def _sort_key(r: RankableRoute) -> tuple:
    """Cascade sort key. Lower is better.

    Values rounded so float noise doesn't invent a false winner.
    """
    m = r.metrics
    return (
        1 if m.blocked else 0,
        round(m.no_travel_miles, 1),
        round(m.severe_miles, 1),
        round(m.high_miles, 1),
        round(m.avg_risk, 3),
        round(r.duration_s, 1),
    )


def recommend(routes: list[RankableRoute]) -> Recommendation:
    """Return the best route and human-readable reasons for the decision."""
    if not routes:
        return Recommendation(route_id="", reasons=["no routes available"], ranking=[])

    ordered = sorted(routes, key=_sort_key)
    ranking = [r.route_id for r in ordered]
    best = ordered[0]

    reasons = _explain(best, ordered)
    return Recommendation(route_id=best.route_id, reasons=reasons, ranking=ranking)


def _explain(best: RankableRoute, ordered: list[RankableRoute]) -> list[str]:
    reasons: list[str] = []
    if best.metrics.blocked:
        reasons.append(
            "All viable routes include No Travel segments; selected least-severe option"
            if all(r.metrics.blocked for r in ordered)
            else "Selected route still contains No Travel miles — travel not advised"
        )

    if len(ordered) == 1:
        reasons.append("Only one route available")
        return reasons

    runner = ordered[1]
    bm, rm = best.metrics, runner.metrics

    if round(bm.severe_miles, 1) < round(rm.severe_miles, 1):
        reasons.append(
            f"fewest Severe miles ({bm.severe_miles:.1f} vs {rm.severe_miles:.1f})"
        )
    elif round(bm.high_miles, 1) < round(rm.high_miles, 1):
        reasons.append(
            f"fewest High miles ({bm.high_miles:.1f} vs {rm.high_miles:.1f})"
        )
    elif round(bm.avg_risk, 3) < round(rm.avg_risk, 3):
        reasons.append(
            f"lowest average risk ({bm.avg_risk:.3f} vs {rm.avg_risk:.3f})"
        )
    elif round(best.duration_s, 1) < round(runner.duration_s, 1):
        reasons.append(
            f"shortest travel time ({best.duration_s / 3600:.2f}h vs {runner.duration_s / 3600:.2f}h)"
        )
    else:
        reasons.append("tied on all criteria; stable sort selected this route")

    if best.metrics.worst_band == RiskBand.LOW:
        reasons.append("entire route is Low risk")

    return reasons
