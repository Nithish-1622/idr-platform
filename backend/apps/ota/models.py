import uuid

from django.db import models


class UpdateManifest(models.Model):
    class PayloadType(models.TextChoices):
        MODEL = "MODEL", "ONNX Model Update"
        MAP = "MAP", "Map Package Update"
        SYSTEM_CONFIG = "SYSTEM_CONFIG", "System Config Update"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payload_type = models.CharField(max_length=20, choices=PayloadType.choices)
    target_version = models.CharField(max_length=50)
    artifact_url = models.CharField(max_length=500)
    checksum_sha256 = models.CharField(max_length=64)
    file_size_bytes = models.BigIntegerField()

    min_app_version = models.CharField(max_length=50, default="1.0.0")
    target_platform = models.CharField(
        max_length=20,
        choices=[("ANDROID", "Android"), ("IOS", "iOS"), ("ALL", "All")],
        default="ALL",
    )
    release_notes = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"OTA Manifest [{self.payload_type}] -> v{self.target_version} ({self.target_platform})"
