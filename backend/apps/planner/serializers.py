from rest_framework import serializers


class PlanTripSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=512)
    destination = serializers.CharField(max_length=512)
    departure = serializers.CharField()
    load_lb = serializers.IntegerField(min_value=1, max_value=200_000)
    interval_mi = serializers.ChoiceField(choices=[10, 25, 50], default=25, required=False)
    origin_lat = serializers.FloatField(required=False, allow_null=True)
    origin_lon = serializers.FloatField(required=False, allow_null=True)
    destination_lat = serializers.FloatField(required=False, allow_null=True)
    destination_lon = serializers.FloatField(required=False, allow_null=True)
    # Loom / calm-forecast helper — injects a synthetic storm corridor
    demo_storm = serializers.BooleanField(required=False, default=False)
