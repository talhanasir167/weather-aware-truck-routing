"""Photon geocoding adapter (keyless)."""

from __future__ import annotations

from dataclasses import dataclass

from apps.core.http import client as http_client


@dataclass
class GeocodeResult:
    label: str
    lat: float
    lon: float
    city: str | None = None
    state: str | None = None
    country: str | None = None


def _format_label(props: dict) -> str:
    parts = [
        props.get("name"),
        props.get("city") or props.get("county"),
        props.get("state"),
        props.get("country"),
    ]
    return ", ".join(p for p in parts if p)


def geocode(query: str, limit: int = 5) -> list[GeocodeResult]:
    """Search Photon for places matching query."""
    query = query.strip()
    if not query:
        return []

    # Accept raw "lat,lon" paste
    if "," in query:
        parts = [p.strip() for p in query.split(",")]
        if len(parts) == 2:
            try:
                lat, lon = float(parts[0]), float(parts[1])
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return [
                        GeocodeResult(
                            label=f"{lat:.5f}, {lon:.5f}",
                            lat=lat,
                            lon=lon,
                        )
                    ]
            except ValueError:
                pass

    from django.conf import settings

    url = f"{settings.PHOTON_BASE_URL}/api"
    params = {"q": query, "limit": limit}
    headers = {"User-Agent": "weather-truck-routing/1.0"}
    with http_client() as client:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    results: list[GeocodeResult] = []
    for feat in data.get("features", []):
        coords = feat.get("geometry", {}).get("coordinates", [])
        props = feat.get("properties", {})
        if len(coords) < 2:
            continue
        lon, lat = float(coords[0]), float(coords[1])
        results.append(
            GeocodeResult(
                label=_format_label(props) or query,
                lat=lat,
                lon=lon,
                city=props.get("city"),
                state=props.get("state"),
                country=props.get("countrycode") or props.get("country"),
            )
        )
    return results
