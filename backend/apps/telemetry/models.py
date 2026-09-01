import uuid

from django.db import models

from apps.devices.models import Device


class TelemetrySession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=128, unique=True, db_index=True)
    device = models.ForeignKey(
        Device, related_name="telemetry_sessions", on_delete=models.CASCADE
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    total_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.session_id[:8]} ({self.device})"


class TelemetryBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch_id = models.CharField(max_length=128, unique=True, db_index=True)
    session = models.ForeignKey(
        TelemetrySession, related_name="batches", on_delete=models.CASCADE
    )
    device = models.ForeignKey(
        Device, related_name="telemetry_batches", on_delete=models.CASCADE
    )
    sequence_number = models.IntegerField(default=1)
    point_count = models.IntegerField(default=0)
    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sequence_number"]

    def __str__(self):
        return f"Batch {self.batch_id[:8]} (Seq: {self.sequence_number})"


class TelemetryPoint(models.Model):
    class NavigationMode(models.TextChoices):
        GNSS = "GNSS", "GNSS Only"
        INS_ONLY = "INS_ONLY", "INS Only"
        AI_IDR_FUSED = "AI_IDR_FUSED", "AI IDR Fused"
        MAP_MATCHED = "MAP_MATCHED", "Map Matched"
        DEGRADED = "DEGRADED", "Degraded"

    class GNSSStatus(models.TextChoices):
        AVAILABLE = "AVAILABLE", "Available"
        DEGRADED = "DEGRADED", "Degraded"
        UNAVAILABLE = "UNAVAILABLE", "Unavailable"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        TelemetryBatch, related_name="points", on_delete=models.CASCADE
    )
    session = models.ForeignKey(
        TelemetrySession, related_name="points", on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(db_index=True)

    latitude = models.FloatField()
    longitude = models.FloatField()
    altitude = models.FloatField(default=0.0)

    velocity = models.FloatField(default=0.0)
    heading = models.FloatField(default=0.0)
    confidence = models.FloatField(default=1.0)

    navigation_mode = models.CharField(
        max_length=30,
        choices=NavigationMode.choices,
        default=NavigationMode.AI_IDR_FUSED,
    )
    gnss_status = models.CharField(
        max_length=30, choices=GNSSStatus.choices, default=GNSSStatus.AVAILABLE
    )

    model_version = models.CharField(max_length=50, blank=True, default="")
    map_version = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["session", "timestamp"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return f"Point ({self.latitude}, {self.longitude}) @ {self.timestamp}"
