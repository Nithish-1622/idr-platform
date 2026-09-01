import pytest
from django.urls import reverse
from rest_framework import status

from apps.devices.models import Device
from apps.telemetry.models import TelemetryBatch, TelemetryPoint, TelemetrySession


@pytest.mark.django_db
def test_telemetry_batch_ingestion_and_idempotency(api_client):
    device = Device.objects.create(
        device_key="telemetry-test-device",
        platform="ANDROID",
        device_model="Galaxy S23",
        os_version="14",
        app_version="1.0.0",
    )

    url = reverse("telemetry:batch_ingest")
    payload = {
        "device_id": str(device.id),
        "session_id": "session-uuid-1001",
        "batch_id": "batch-uuid-5001",
        "sequence_number": 1,
        "points": [
            {
                "timestamp": "2026-09-02T10:00:00Z",
                "latitude": 12.9716,
                "longitude": 77.5946,
                "altitude": 920.5,
                "velocity": 5.4,
                "heading": 180.0,
                "confidence": 0.98,
                "navigation_mode": "AI_IDR_FUSED",
                "gnss_status": "AVAILABLE",
                "model_version": "1.0.0",
                "map_version": "2026.01",
            },
            {
                "timestamp": "2026-09-02T10:00:01Z",
                "latitude": 12.9717,
                "longitude": 77.5947,
                "altitude": 920.6,
                "velocity": 5.5,
                "heading": 180.5,
                "confidence": 0.97,
                "navigation_mode": "AI_IDR_FUSED",
                "gnss_status": "AVAILABLE",
                "model_version": "1.0.0",
                "map_version": "2026.01",
            },
        ],
    }

    # First upload -> 201 Created
    response1 = api_client.post(url, payload, format="json")
    assert response1.status_code == status.HTTP_201_CREATED
    assert response1.data["points_ingested"] == 2
    assert response1.data["duplicate_ignored"] is False

    # Check DB state
    assert TelemetrySession.objects.filter(session_id="session-uuid-1001").exists()
    assert TelemetryBatch.objects.filter(batch_id="batch-uuid-5001").exists()
    assert TelemetryPoint.objects.count() == 2

    # Second upload of same batch (Retry scenario) -> 200 OK & duplicate_ignored=True
    response2 = api_client.post(url, payload, format="json")
    assert response2.status_code == status.HTTP_200_OK
    assert response2.data["duplicate_ignored"] is True
    assert TelemetryPoint.objects.count() == 2  # No duplicates created
