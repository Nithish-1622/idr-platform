from rest_framework import serializers

from .models import TelemetryPoint, TelemetrySession


class TelemetryPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemetryPoint
        fields = [
            "timestamp",
            "latitude",
            "longitude",
            "altitude",
            "velocity",
            "heading",
            "confidence",
            "navigation_mode",
            "gnss_status",
            "model_version",
            "map_version",
        ]


class TelemetryBatchIngestSerializer(serializers.Serializer):
    device_id = serializers.UUIDField()
    session_id = serializers.CharField(max_length=128)
    batch_id = serializers.CharField(max_length=128)
    sequence_number = serializers.IntegerField(default=1)
    points = TelemetryPointSerializer(many=True)

    def validate_points(self, value):
        if not value:
            raise serializers.ValidationError(
                "Telemetry batch must contain at least one point."
            )
        return value


class TelemetrySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemetrySession
        fields = [
            "id",
            "session_id",
            "device",
            "start_time",
            "end_time",
            "total_points",
            "created_at",
        ]
