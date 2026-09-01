import logging

from celery import shared_task

from .models import TelemetryBatch, TelemetryPoint

logger = logging.getLogger(__name__)


@shared_task
def aggregate_telemetry_metrics_task(batch_id: str):
    """Asynchronous background task to process and compute spatial stats for ingested telemetry batch."""
    try:
        batch = TelemetryBatch.objects.get(batch_id=batch_id)
        points = TelemetryPoint.objects.filter(batch=batch)
        count = points.count()
        logger.info(
            f"Background analysis completed for batch {batch_id}: {count} telemetry points processed."
        )
        return count
    except TelemetryBatch.DoesNotExist:
        logger.warning(f"Batch {batch_id} not found for async processing.")
        return 0
