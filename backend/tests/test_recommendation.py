from apps.risk.aggregate import RouteMetrics
from apps.risk.bands import RiskBand
from apps.risk.recommend import RankableRoute, recommend


def _route(rid, severe=0, high=0, avg=0.5, dur=3600, no_travel=0):
    m = RouteMetrics(
        severe_miles=severe,
        high_miles=high,
        avg_risk=avg,
        no_travel_miles=no_travel,
        blocked=no_travel > 0,
        worst_band=RiskBand.SEVERE if severe else (RiskBand.HIGH if high else RiskBand.LOW),
        total_miles=100,
    )
    return RankableRoute(route_id=rid, metrics=m, duration_s=dur)


def test_fewest_severe_wins():
    routes = [_route("a", severe=10), _route("b", severe=0), _route("c", severe=5)]
    rec = recommend(routes)
    assert rec.route_id == "b"
    assert any("Severe" in r for r in rec.reasons)


def test_high_breaks_severe_tie():
    routes = [_route("a", severe=0, high=20), _route("b", severe=0, high=5)]
    rec = recommend(routes)
    assert rec.route_id == "b"
    assert any("High" in r for r in rec.reasons)


def test_avg_risk_breaks_high_tie():
    routes = [
        _route("a", severe=0, high=5, avg=1.2),
        _route("b", severe=0, high=5, avg=0.4),
    ]
    rec = recommend(routes)
    assert rec.route_id == "b"
    assert any("average risk" in r for r in rec.reasons)


def test_duration_breaks_avg_tie():
    routes = [
        _route("a", severe=0, high=0, avg=0.5, dur=7200),
        _route("b", severe=0, high=0, avg=0.5, dur=3600),
    ]
    rec = recommend(routes)
    assert rec.route_id == "b"
    assert any("travel time" in r for r in rec.reasons)


def test_blocked_demoted():
    routes = [
        _route("safe", severe=5, no_travel=0),
        _route("blocked", severe=0, no_travel=10),
    ]
    rec = recommend(routes)
    assert rec.route_id == "safe"


def test_all_blocked_still_picks_least_bad():
    routes = [
        _route("a", no_travel=20, severe=0),
        _route("b", no_travel=5, severe=0),
    ]
    rec = recommend(routes)
    assert rec.route_id == "b"
    assert any("No Travel" in r for r in rec.reasons)


def test_near_tie_rounding():
    # 0.04 mi difference rounds to same 0.1 → falls through to high
    routes = [
        _route("a", severe=1.04, high=10),
        _route("b", severe=1.00, high=0),
    ]
    rec = recommend(routes)
    # After rounding severe to 1.0 both, high decides → b
    assert rec.route_id == "b"


def test_empty_routes():
    rec = recommend([])
    assert rec.route_id == ""
