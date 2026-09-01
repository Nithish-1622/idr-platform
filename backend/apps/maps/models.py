import uuid

from django.db import models


class MapPackage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    region_code = models.CharField(max_length=50, db_index=True)
    version = models.CharField(max_length=50)
    checksum_sha256 = models.CharField(max_length=64)
    file_size_bytes = models.BigIntegerField()
    file_path = models.FileField(upload_to="maps/packages/")

    min_latitude = models.FloatField()
    max_latitude = models.FloatField()
    min_longitude = models.FloatField()
    max_longitude = models.FloatField()

    is_active = models.BooleanField(default=True)
    compatibility_min_app_version = models.CharField(max_length=50, default="1.0.0")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("region_code", "version")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Map {self.name} [{self.region_code}] v{self.version}"


class MapRegion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150)
    country_code = models.CharField(max_length=10, default="IND")
    bounding_box = models.JSONField(
        default=dict, help_text="{'min_lat', 'max_lat', 'min_lng', 'max_lng'}"
    )

    def __str__(self):
        return f"{self.name} ({self.code})"
