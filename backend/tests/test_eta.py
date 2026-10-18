import pytest

from apps.geo.polyline import LatLon
from apps.routing.eta import eta_at_distance


def test_etas_increasing():
    geom = [LatLon(40, -90), LatLon(40, -89), LatLon(40, -88)]
    cum_mi = [0.0, 50.0, 100.0]
    cum_s = [0.0, 3600.0, 7200.0]
    dep = "2026-10-17T12:00:00Z"
    d1, e1 = eta_at_distance(25, dep, geom, cum_mi, cum_s)
    d2, e2 = eta_at_distance(75, dep, geom, cum_mi, cum_s)
    assert d1 < d2
    assert e1 < e2


def test_naive_datetime_rejected():
    geom = [LatLon(40, -90), LatLon(40, -88)]
    with pytest.raises(ValueError, match="timezone-aware"):
        eta_at_distance(10, "2026-10-17T12:00:00", geom)
