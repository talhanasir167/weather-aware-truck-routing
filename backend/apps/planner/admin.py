from django.contrib import admin

from .models import Checkpoint, RoutePlan, Trip


class RouteInline(admin.TabularInline):
    model = RoutePlan
    extra = 0


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ("id", "origin_label", "destination_label", "load_lb", "created_at")
    inlines = [RouteInline]


@admin.register(RoutePlan)
class RoutePlanAdmin(admin.ModelAdmin):
    list_display = ("route_key", "trip", "distance_m", "duration_s", "is_recommended")


@admin.register(Checkpoint)
class CheckpointAdmin(admin.ModelAdmin):
    list_display = ("route", "index", "band", "distance_mi", "eta_utc")
