from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import AppError
from apps.geo.service import geocode
from apps.planner.models import Trip
from apps.planner.serializers import PlanTripSerializer
from apps.planner.service import plan_trip, trip_to_dict


class PlanTripView(APIView):
    def post(self, request: Request) -> Response:
        ser = PlanTripSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        trip = plan_trip(
            origin=data["origin"],
            destination=data["destination"],
            departure=data["departure"],
            load_lb=data["load_lb"],
            interval_mi=data.get("interval_mi", 25),
            origin_lat=data.get("origin_lat"),
            origin_lon=data.get("origin_lon"),
            destination_lat=data.get("destination_lat"),
            destination_lon=data.get("destination_lon"),
            demo_storm=bool(data.get("demo_storm", False)),
        )
        return Response(trip_to_dict(trip), status=status.HTTP_201_CREATED)


class TripDetailView(APIView):
    def get(self, request: Request, trip_id: str) -> Response:
        try:
            trip = Trip.objects.prefetch_related("routes__checkpoints").get(id=trip_id)
        except (Trip.DoesNotExist, ValueError) as exc:
            raise AppError("Trip not found", code="not_found", status_code=404) from exc
        return Response(trip_to_dict(trip))


class GeocodeView(APIView):
    def get(self, request: Request) -> Response:
        q = request.query_params.get("q", "").strip()
        if len(q) < 3 and "," not in q:
            return Response({"results": []})
        results = geocode(q, limit=5)
        return Response(
            {
                "results": [
                    {
                        "label": r.label,
                        "lat": r.lat,
                        "lon": r.lon,
                        "city": r.city,
                        "state": r.state,
                        "country": r.country,
                    }
                    for r in results
                ]
            }
        )
