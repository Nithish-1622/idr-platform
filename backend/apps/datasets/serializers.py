from rest_framework import serializers

from .models import Dataset, DatasetVersion


class DatasetVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetVersion
        fields = [
            "id",
            "dataset",
            "version",
            "checksum_sha256",
            "file_format",
            "sampling_rate_hz",
            "file_size_bytes",
            "file_path",
            "validation_status",
            "metadata",
            "uploaded_at",
        ]
        read_only_fields = ["id", "checksum_sha256", "file_size_bytes", "uploaded_at"]


class DatasetSerializer(serializers.ModelSerializer):
    versions = DatasetVersionSerializer(many=True, read_only=True)

    class Meta:
        model = Dataset
        fields = [
            "id",
            "name",
            "description",
            "source",
            "versions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
