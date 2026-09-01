import pytest
from django.urls import reverse
from rest_framework import status

from apps.configurations.models import SystemConfiguration


@pytest.mark.django_db
def test_configurations_and_sync_check(api_client):
    SystemConfiguration.objects.create(
        key="telemetry_upload_interval_sec",
        value={"interval": 30},
        description="Interval for mobile telemetry batch uploads",
    )

    url_config = reverse("configurations:list")
    res_config = api_client.get(url_config)
    assert res_config.status_code == status.HTTP_200_OK
    assert "telemetry_upload_interval_sec" in res_config.data
    assert res_config.data["telemetry_upload_interval_sec"]["interval"] == 30

    url_sync = reverse("configurations:sync_check")
    res_sync = api_client.get(url_sync, {"platform": "ANDROID"})
    assert res_sync.status_code == status.HTTP_200_OK
    assert "configurations" in res_sync.data
    assert "latest_model_version" in res_sync.data
