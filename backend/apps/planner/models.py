"""Persisted trip plans for shareable reload-stable results."""

from __future__ import annotations

import uuid

from django.db import models


class Trip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    origin_label = models.CharField(max_length=512)
    origin_lat = models.FloatField()
    origin_lon = models.FloatField()
    destination_label = models.CharField(max_length=512)
    destination_lat = models.FloatField()
    destination_lon = models.FloatField()
    departure_utc = models.DateTimeField()
    load_lb = models.PositiveIntegerField()
    interval_mi = models.PositiveSmallIntegerField(default=25)
    recommended_route_id = models.CharField(max_length=64, blank=True)
    recommendation_reasons = models.JSONField(default=list)
    degraded = models.JSONField(default=list)
    meta = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class RoutePlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trip = models.ForeignKey(Trip, related_name="routes", on_delete=models.CASCADE)
    route_key = models.CharField(max_length=64)  # e.g. route_0
    provider = models.CharField(max_length=32, blank=True)
    distance_m = models.FloatField()
    duration_s = models.FloatField()
    geometry = models.JSONField(default=list)  # [[lon, lat], ...]
    metrics = models.JSONField(default=dict)
    summary = models.CharField(max_length=256, blank=True)
    is_recommended = models.BooleanField(default=False)
    rank = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["rank"]


class Checkpoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    route = models.ForeignKey(RoutePlan, related_name="checkpoints", on_delete=models.CASCADE)
    index = models.PositiveIntegerField()
    lat = models.FloatField()
    lon = models.FloatField()
    distance_mi = models.FloatField()
    eta_utc = models.DateTimeField()
    segment_miles = models.FloatField(default=0)
    band = models.CharField(max_length=32)
    wind_mph = models.FloatField(default=0)
    wind_gusts_mph = models.FloatField(default=0)
    rain_in_hr = models.FloatField(default=0)
    snow_in_hr = models.FloatField(default=0)
    weather_available = models.BooleanField(default=True)
    reasons = models.JSONField(default=dict)

    class Meta:
        ordering = ["index"]
