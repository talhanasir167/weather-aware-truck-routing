"""Nominatim geocoding fallback (requires User-Agent, 1 req/s)."""

from __future__ import annotations

from apps.core.http import client as http_client

from .photon import GeocodeResult


def geocode(query: str, limit: int = 5) -> list[GeocodeResult]:
    query = query.strip()
    if not query:
        return []
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": limit}
    headers = {"User-Agent": "weather-truck-routing/1.0 (assessment)"}
    with http_client() as client:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    results: list[GeocodeResult] = []
    for item in data:
        results.append(
            GeocodeResult(
                label=item.get("display_name", query),
                lat=float(item["lat"]),
                lon=float(item["lon"]),
            )
        )
    return results
