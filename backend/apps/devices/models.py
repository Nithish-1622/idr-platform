import uuid

from django.db import models


class Device(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "ANDROID", "Android"
        IOS = "IOS", "iOS"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"
        REVOKED = "REVOKED", "Revoked"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_key = models.CharField(max_length=128, unique=True, db_index=True)
    platform = models.CharField(max_length=20, choices=Platform.choices)
    device_model = models.CharField(max_length=100)
    os_version = models.CharField(max_length=50)
    app_version = models.CharField(max_length=50)

    imu_capabilities = models.JSONField(default=dict, blank=True)
    sensor_capabilities = models.JSONField(default=dict, blank=True)

    active_model_version = models.CharField(max_length=50, blank=True, default="")
    active_map_version = models.CharField(max_length=50, blank=True, default="")

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    last_seen_at = models.DateTimeField(auto_now=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-registered_at"]
        indexes = [
            models.Index(fields=["platform", "status"]),
            models.Index(fields=["last_seen_at"]),
        ]

    def __str__(self):
        return f"{self.device_model} ({self.platform}) - {self.device_key[:8]}"
