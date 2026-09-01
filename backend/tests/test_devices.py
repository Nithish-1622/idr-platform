import pytest
from django.urls import reverse
from rest_framework import status

from apps.devices.models import Device


@pytest.mark.django_db
def test_device_registration(api_client):
    url = reverse("devices:register")
    payload = {
        "device_key": "unique-device-key-12345",
        "platform": "ANDROID",
        "device_model": "Pixel 8 Pro",
        "os_version": "14.0",
        "app_version": "1.0.0",
        "imu_capabilities": {"accel_hz": 200, "gyro_hz": 200},
        "sensor_capabilities": {"has_barometer": True},
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["device_key"] == "unique-device-key-12345"
    assert Device.objects.filter(device_key="unique-device-key-12345").exists()


@pytest.mark.django_db
def test_device_heartbeat(api_client):
    device = Device.objects.create(
        device_key="heartbeat-device-key",
        platform="IOS",
        device_model="iPhone 15 Pro",
        os_version="17.2",
        app_version="1.0.0",
    )
    url = reverse("devices:heartbeat", kwargs={"pk": str(device.id)})
    payload = {"app_version": "1.0.1", "active_model_version": "1.2.0"}
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    device.refresh_from_db()
    assert device.app_version == "1.0.1"
    assert device.active_model_version == "1.2.0"
