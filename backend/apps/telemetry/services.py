import logging

from django.db import transaction

from apps.devices.models import Device

from .models import TelemetryBatch, TelemetryPoint, TelemetrySession

logger = logging.getLogger(__name__)


def ingest_telemetry_batch_service(validated_data: dict) -> tuple[TelemetryBatch, bool]:
    """
    Idempotently ingests a telemetry batch.
    If the batch_id has already been processed, returns existing batch (created=False).
    """
    device_id = validated_data["device_id"]
    session_id_str = validated_data["session_id"]
    batch_id_str = validated_data["batch_id"]
    seq = validated_data["sequence_number"]
    points_data = validated_data["points"]

    # Idempotency check: if batch already exists, return existing
    existing_batch = TelemetryBatch.objects.filter(batch_id=batch_id_str).first()
    if existing_batch:
        logger.info(
            f"Telemetry batch {batch_id_str} already ingested. Returning existing record."
        )
        return existing_batch, False

    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        raise ValueError(f"Device with ID {device_id} does not exist.")

    with transaction.atomic():
        # Retrieve or create session
        first_point_time = points_data[0]["timestamp"]
        session, _ = TelemetrySession.objects.get_or_create(
            session_id=session_id_str,
            defaults={
                "device": device,
                "start_time": first_point_time,
                "total_points": 0,
            },
        )

        batch = TelemetryBatch.objects.create(
            batch_id=batch_id_str,
            session=session,
            device=device,
            sequence_number=seq,
            point_count=len(points_data),
        )

        point_objects = [
            TelemetryPoint(
                batch=batch,
                session=session,
                timestamp=p["timestamp"],
                latitude=p["latitude"],
                longitude=p["longitude"],
                altitude=p.get("altitude", 0.0),
                velocity=p.get("velocity", 0.0),
                heading=p.get("heading", 0.0),
                confidence=p.get("confidence", 1.0),
                navigation_mode=p.get("navigation_mode", "AI_IDR_FUSED"),
                gnss_status=p.get("gnss_status", "AVAILABLE"),
                model_version=p.get("model_version", ""),
                map_version=p.get("map_version", ""),
            )
            for p in points_data
        ]
        TelemetryPoint.objects.bulk_create(point_objects)

        # Update session totals
        session.total_points += len(points_data)
        session.end_time = points_data[-1]["timestamp"]
        session.save(update_fields=["total_points", "end_time"])

        return batch, True
