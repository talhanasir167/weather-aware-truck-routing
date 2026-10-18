from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import AppError
from apps.heatmap.service import build_heatmap
from apps.planner.models import Trip


class HeatmapView(APIView):
    def get(self, request: Request, trip_id: str) -> Response:
        try:
            trip = Trip.objects.prefetch_related("routes").get(id=trip_id)
        except (Trip.DoesNotExist, ValueError) as exc:
            raise AppError("Trip not found", code="not_found", status_code=404) from exc
        return Response(build_heatmap(trip))
