from django.utils import timezone

from .models import Device


def register_device_service(data: dict) -> Device:
    """Service to register a new device or update existing device details by device_key."""
    device_key = data.get("device_key")
    device, created = Device.objects.update_or_create(
        device_key=device_key, defaults=data
    )
    return device


def update_device_heartbeat_service(device: Device, heartbeat_data: dict) -> Device:
    """Updates device last_seen timestamp and active version metadata."""
    for field in ["app_version", "active_model_version", "active_map_version"]:
        if field in heartbeat_data and heartbeat_data[field]:
            setattr(device, field, heartbeat_data[field])
    device.last_seen_at = timezone.now()
    device.save(
        update_fields=[
            "app_version",
            "active_model_version",
            "active_map_version",
            "last_seen_at",
        ]
    )
    return device
