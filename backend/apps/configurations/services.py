from apps.maps.models import MapPackage
from apps.models.models import Deployment

from .models import DeviceConfiguration, SystemConfiguration


def get_effective_config_service(device_key: str = None) -> dict:
    """Returns effective key-value configuration dictionary."""
    config_dict = {}
    for sys_config in SystemConfiguration.objects.filter(is_active=True):
        config_dict[sys_config.key] = sys_config.value

    if device_key:
        device_overrides = DeviceConfiguration.objects.filter(
            device__device_key=device_key
        )
        for override in device_overrides:
            config_dict[override.key] = override.value

    return config_dict


def get_device_sync_status_service(device_key: str, platform: str) -> dict:
    """
    Evaluates latest available models, maps, system configs for a device sync check.
    Allows mobile edge to check status without heavy payload downloads.
    """
    configs = get_effective_config_service(device_key)

    active_deployment = (
        Deployment.objects.filter(is_active=True, target_platform__in=[platform, "ALL"])
        .select_related("model_version")
        .first()
    )

    latest_model_ver = (
        active_deployment.model_version.semantic_version if active_deployment else "N/A"
    )

    latest_map = MapPackage.objects.filter(is_active=True).first()
    latest_map_ver = latest_map.version if latest_map else "N/A"

    return {
        "configurations": configs,
        "latest_model_version": latest_model_ver,
        "latest_map_version": latest_map_ver,
        "force_app_update": configs.get("min_supported_app_version", "1.0.0"),
    }
