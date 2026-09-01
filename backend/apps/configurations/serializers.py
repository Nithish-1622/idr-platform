from rest_framework import serializers

from .models import SystemConfiguration


class SystemConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = ["key", "value", "description", "updated_at"]


class DeviceSyncStatusSerializer(serializers.Serializer):
    device_id = serializers.UUIDField()
    app_version = serializers.CharField()
    active_model_version = serializers.CharField()
    active_map_version = serializers.CharField()
