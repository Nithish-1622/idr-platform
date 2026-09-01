import pytest
from django.urls import reverse
from rest_framework import status

from apps.ota.models import UpdateManifest


@pytest.mark.django_db
def test_ota_update_check(api_client):
    manifest = UpdateManifest.objects.create(
        payload_type="MAP",
        target_version="2026.02",
        artifact_url="https://idr-storage.local/maps/2026.02.mbtiles",
        checksum_sha256="b" * 64,
        file_size_bytes=5242880,
        min_app_version="1.0.0",
        target_platform="ANDROID",
        release_notes="Updated Bengaluru road network",
    )

    url = reverse("ota:check")
    payload = {
        "platform": "ANDROID",
        "app_version": "1.0.0",
        "current_model_version": "1.0.0",
        "current_map_version": "2026.01",
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "available_updates" in response.data
    updates = response.data["available_updates"]
    assert len(updates) >= 1
    assert updates[0]["target_version"] == "2026.02"
