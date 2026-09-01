from django.db.models import Avg, Count

from apps.devices.models import Device
from apps.models.models import ModelMetric
from apps.telemetry.models import TelemetryPoint, TelemetrySession


def get_telemetry_analytics_summary() -> dict:
    """Computes high-level backend telemetry analytics summary."""
    total_devices = Device.objects.count()
    active_devices = Device.objects.filter(status=Device.Status.ACTIVE).count()
    total_sessions = TelemetrySession.objects.count()
    total_points = TelemetryPoint.objects.count()

    nav_mode_distribution = list(
        TelemetryPoint.objects.values("navigation_mode")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    avg_confidence = (
        TelemetryPoint.objects.aggregate(avg_conf=Avg("confidence"))["avg_conf"] or 0.0
    )

    return {
        "devices": {"total": total_devices, "active": active_devices},
        "telemetry": {
            "total_sessions": total_sessions,
            "total_points": total_points,
            "avg_confidence": round(avg_confidence, 4),
            "mode_distribution": nav_mode_distribution,
        },
    }


def get_model_performance_analytics() -> dict:
    """Computes model performance distribution from logged TelemetryPoint data and ModelMetrics."""
    model_usage = list(
        TelemetryPoint.objects.exclude(model_version="")
        .values("model_version")
        .annotate(point_count=Count("id"), avg_confidence=Avg("confidence"))
        .order_by("-point_count")
    )

    metrics = list(
        ModelMetric.objects.values(
            "model_version__semantic_version",
            "metric_name",
            "metric_value",
            "dataset_name",
        )
    )

    return {"usage_by_version": model_usage, "recorded_model_metrics": metrics}
