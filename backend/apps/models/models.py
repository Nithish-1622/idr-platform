import uuid

from django.db import models


class MLModel(models.Model):
    class ModelType(models.TextChoices):
        IDR_RECURRENT = "IDR_RECURRENT", "Recurrent Neural Network (LSTM/GRU)"
        IDR_TRANSFORMER = "IDR_TRANSFORMER", "Temporal Transformer"
        IDR_EKF_HYBRID = "IDR_EKF_HYBRID", "Hybrid EKF + AI Model"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    model_type = models.CharField(max_length=50, choices=ModelType.choices)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.model_type})"


class ModelVersion(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        VALIDATING = "VALIDATING", "Validating"
        APPROVED = "APPROVED", "Approved"
        ACTIVE = "ACTIVE", "Active Deployment"
        DEPRECATED = "DEPRECATED", "Deprecated"
        REVOKED = "REVOKED", "Revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ml_model = models.ForeignKey(
        MLModel, related_name="versions", on_delete=models.CASCADE
    )
    semantic_version = models.CharField(max_length=50)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )

    # Compatibility specifications
    min_app_version = models.CharField(max_length=50, default="1.0.0")
    supported_platforms = models.JSONField(default=list, help_text="['ANDROID', 'IOS']")
    sensor_profile_requirements = models.JSONField(default=dict, blank=True)

    input_schema = models.JSONField(default=dict)
    output_schema = models.JSONField(default=dict)

    # ML Contract specifications
    opset_version = models.IntegerField(default=14, help_text="ONNX Opset version")
    preprocessing_spec = models.JSONField(default=dict, blank=True, help_text="Preprocessing steps from contracts/model/preprocessing.json")
    contract_spec = models.JSONField(default=dict, blank=True, help_text="Canonical contract schema spec")

    release_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("ml_model", "semantic_version")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ml_model.name} v{self.semantic_version} [{self.status}]"


class ModelArtifact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_version = models.OneToOneField(
        ModelVersion, related_name="artifact", on_delete=models.CASCADE
    )
    format = models.CharField(max_length=20, default="ONNX")
    file_path = models.FileField(upload_to="models/onnx/")
    checksum_sha256 = models.CharField(max_length=64)
    file_size_bytes = models.BigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Artifact for {self.model_version}"


class ModelMetric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_version = models.ForeignKey(
        ModelVersion, related_name="metrics", on_delete=models.CASCADE
    )
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    dataset_name = models.CharField(max_length=150, blank=True, default="")

    def __str__(self):
        return f"{self.metric_name}={self.metric_value} ({self.model_version})"


class Deployment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_version = models.ForeignKey(
        ModelVersion, related_name="deployments", on_delete=models.CASCADE
    )
    target_platform = models.CharField(
        max_length=20, choices=[("ANDROID", "Android"), ("IOS", "iOS"), ("ALL", "All")]
    )
    is_active = models.BooleanField(default=True)
    deployed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Deployment v{self.model_version.semantic_version} -> {self.target_platform}"
