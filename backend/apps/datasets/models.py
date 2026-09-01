import uuid

from django.db import models


class Dataset(models.Model):
    class ValidationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Validation"
        VALIDATED = "VALIDATED", "Validated"
        FAILED = "FAILED", "Validation Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)
    source = models.CharField(
        max_length=150, help_text="Source vehicle/device/environment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class DatasetVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dataset = models.ForeignKey(
        Dataset, related_name="versions", on_delete=models.CASCADE
    )
    version = models.CharField(max_length=50)
    checksum_sha256 = models.CharField(max_length=64)
    file_format = models.CharField(max_length=20, default="HDF5")
    sampling_rate_hz = models.FloatField(default=100.0)
    file_size_bytes = models.BigIntegerField(default=0)
    file_path = models.FileField(upload_to="datasets/")
    validation_status = models.CharField(
        max_length=20,
        choices=Dataset.ValidationStatus.choices,
        default=Dataset.ValidationStatus.PENDING,
    )
    metadata = models.JSONField(default=dict, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("dataset", "version")

    def __str__(self):
        return f"{self.dataset.name} v{self.version}"
