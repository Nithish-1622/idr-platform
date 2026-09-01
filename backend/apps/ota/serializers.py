from rest_framework import serializers

from .models import UpdateManifest


class OTACheckRequestSerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=["ANDROID", "IOS"])
    app_version = serializers.CharField()
    current_model_version = serializers.CharField(required=False, allow_blank=True)
    current_map_version = serializers.CharField(required=False, allow_blank=True)


class UpdateManifestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpdateManifest
        fields = [
            "id",
            "payload_type",
            "target_version",
            "artifact_url",
            "checksum_sha256",
            "file_size_bytes",
            "min_app_version",
            "target_platform",
            "release_notes",
            "is_mandatory",
            "created_at",
        ]
