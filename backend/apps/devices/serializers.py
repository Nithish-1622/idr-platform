from rest_framework import serializers

from .models import Device


class DeviceRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            "device_key",
            "platform",
            "device_model",
            "os_version",
            "app_version",
            "imu_capabilities",
            "sensor_capabilities",
            "active_model_version",
            "active_map_version",
        ]


class DeviceDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = "__all__"
        read_only_fields = ["id", "registered_at", "last_seen_at"]


class DeviceHeartbeatSerializer(serializers.Serializer):
    app_version = serializers.CharField(required=False)
    active_model_version = serializers.CharField(required=False)
    active_map_version = serializers.CharField(required=False)
