import uuid
from django.db import models


class SimulationRun(models.Model):
    class Status(models.TextChoices):
        CREATED = "CREATED", "Created"
        QUEUED = "QUEUED", "Queued"
        RUNNING = "RUNNING", "Running"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    scenario_id = models.CharField(max_length=150)
    scenario_name = models.CharField(max_length=200, blank=True, default="")
    seed = models.IntegerField(default=42)
    duration_seconds = models.FloatField(default=300.0)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.CREATED
    )
    scenario_config = models.JSONField(default=dict, blank=True)

    metrics = models.JSONField(default=dict, blank=True)
    gnss_outage_evaluations = models.JSONField(default=list, blank=True)
    artifact_paths = models.JSONField(default=dict, blank=True)

    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Simulation {self.scenario_id} [{self.status}] ({self.id})"
