"""Geocode service: Photon primary, Nominatim fallback."""

from unittest.mock import patch

from apps.geo.providers.photon import GeocodeResult
from apps.geo.service import geocode


def test_photon_success_skips_nominatim():
    hit = [GeocodeResult(label="Chicago, IL", lat=41.88, lon=-87.63)]
    with (
        patch("apps.geo.service.photon.geocode", return_value=hit) as photon,
        patch("apps.geo.service.nominatim.geocode") as nomi,
    ):
        out = geocode("Chicago")
    assert out == hit
    photon.assert_called_once()
    nomi.assert_not_called()


def test_empty_photon_falls_back_to_nominatim():
    fallback = [GeocodeResult(label="Detroit, MI", lat=42.33, lon=-83.05)]
    with (
        patch("apps.geo.service.photon.geocode", return_value=[]),
        patch("apps.geo.service.nominatim.geocode", return_value=fallback) as nomi,
    ):
        out = geocode("Detroit")
    assert out == fallback
    nomi.assert_called_once()


def test_photon_error_falls_back_to_nominatim():
    fallback = [GeocodeResult(label="X", lat=1.0, lon=2.0)]
    with (
        patch("apps.geo.service.photon.geocode", side_effect=RuntimeError("down")),
        patch("apps.geo.service.nominatim.geocode", return_value=fallback),
    ):
        out = geocode("somewhere")
    assert out == fallback


def test_both_providers_fail_returns_empty():
    with (
        patch("apps.geo.service.photon.geocode", side_effect=RuntimeError("p")),
        patch("apps.geo.service.nominatim.geocode", side_effect=RuntimeError("n")),
    ):
        assert geocode("nowhere") == []
