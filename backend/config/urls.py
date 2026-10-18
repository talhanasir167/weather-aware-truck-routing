from django.contrib import admin
from django.urls import path

from apps.core.views import healthz, status
from apps.heatmap.views import HeatmapView
from apps.planner.views import GeocodeView, PlanTripView, TripDetailView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/healthz", healthz, name="healthz"),
    path("api/v1/status", status, name="status"),
    path("api/v1/geocode", GeocodeView.as_view(), name="geocode"),
    path("api/v1/trips/plan", PlanTripView.as_view(), name="plan_trip"),
    path("api/v1/trips/<uuid:trip_id>", TripDetailView.as_view(), name="trip_detail"),
    path("api/v1/trips/<uuid:trip_id>/heatmap", HeatmapView.as_view(), name="heatmap"),
]
