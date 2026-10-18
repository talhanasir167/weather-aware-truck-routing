from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def healthz(_request):
    return JsonResponse({"status": "ok"})


@require_GET
def status(_request):
    """Public capability flags for the UI (no secrets)."""
    ors_key = (settings.ORS_API_KEY or "").strip()
    return JsonResponse(
        {
            "status": "ok",
            "ors_configured": bool(ors_key),
            "routing": {
                "primary": "openrouteservice_driving-hgv" if ors_key else "osrm_fallback",
                "fallback": "osrm",
            },
            "weather": "open-meteo",
            "geocoding": "photon",
            "demo_storm_available": True,
        }
    )
