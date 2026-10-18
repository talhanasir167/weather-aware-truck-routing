from datetime import datetime, timedelta, timezone

import pytest
from django.core.cache import cache
from freezegun import freeze_time

from apps.weather import cache as wx_cache


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


def test_snap_grid_rounds_to_tenth():
    assert wx_cache.snap_grid(41.878, -87.629) == (41.9, -87.6)


def test_grid_key_floors_to_hour():
    key = wx_cache.grid_key(41.9, -87.6, "2026-10-17T12:34:56Z")
    assert key == "wx:v1:41.90:-87.60:2026-10-17T12"


@freeze_time("2026-10-17T12:00:00Z")
def test_set_and_get_many_roundtrip():
    key = wx_cache.grid_key(41.9, -87.6, "2026-10-17T15:00:00Z")
    payload = {"wind_mph": 12.0, "rain_in_hr": 0.0}
    wx_cache.set_many({key: payload})
    got = wx_cache.get_many([key, "missing"])
    assert got[key]["wind_mph"] == 12.0
    assert "missing" not in got


@freeze_time("2026-10-17T12:00:00Z")
def test_far_hour_uses_longer_ttl_path():
    """Far-term hours still cache (TTL branch exercised; value is readable)."""
    far = (datetime(2026, 10, 17, 12, tzinfo=timezone.utc) + timedelta(hours=36)).strftime(
        "%Y-%m-%dT%H:00:00Z"
    )
    key = wx_cache.grid_key(40.0, -90.0, far)
    wx_cache.set_many({key: {"wind_mph": 20.0}})
    assert wx_cache.get_many([key])[key]["wind_mph"] == 20.0
