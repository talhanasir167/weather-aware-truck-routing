"""Geocoding service with Photon primary and Nominatim fallback."""

from __future__ import annotations

import logging

from .providers import nominatim, photon
from .providers.photon import GeocodeResult

logger = logging.getLogger(__name__)


def geocode(query: str, limit: int = 5) -> list[GeocodeResult]:
    try:
        results = photon.geocode(query, limit=limit)
        if results:
            return results
    except Exception:
        logger.exception("Photon geocode failed; falling back to Nominatim")
    try:
        return nominatim.geocode(query, limit=limit)
    except Exception:
        logger.exception("Nominatim geocode also failed")
        return []
