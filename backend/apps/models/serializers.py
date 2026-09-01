from rest_framework import serializers

from .models import Deployment, MLModel, ModelArtifact, ModelMetric, ModelVersion


class ModelArtifactSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelArtifact
        fields = [
            "id",
            "format",
            "file_path",
            "checksum_sha256",
            "file_size_bytes",
            "uploaded_at",
        ]
        read_only_fields = ["id", "checksum_sha256", "file_size_bytes", "uploaded_at"]


class ModelMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelMetric
        fields = ["metric_name", "metric_value", "dataset_name"]


class ModelVersionSerializer(serializers.ModelSerializer):
    artifact = ModelArtifactSerializer(read_only=True)
    metrics = ModelMetricSerializer(many=True, read_only=True)

    class Meta:
        model = ModelVersion
        fields = [
            "id",
            "ml_model",
            "semantic_version",
            "status",
            "min_app_version",
            "supported_platforms",
            "sensor_profile_requirements",
            "input_schema",
            "output_schema",
            "artifact",
            "metrics",
            "release_date",
            "created_at",
        ]
        read_only_fields = ["id", "status", "created_at"]


class MLModelSerializer(serializers.ModelSerializer):
    versions = ModelVersionSerializer(many=True, read_only=True)

    class Meta:
        model = MLModel
        fields = ["id", "name", "model_type", "description", "versions", "created_at"]
        read_only_fields = ["id", "created_at"]


class DeploymentSerializer(serializers.ModelSerializer):
    model_version_details = ModelVersionSerializer(
        source="model_version", read_only=True
    )

    class Meta:
        model = Deployment
        fields = [
            "id",
            "model_version",
            "model_version_details",
            "target_platform",
            "is_active",
            "deployed_at",
        ]
        read_only_fields = ["id", "deployed_at"]
