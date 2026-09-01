from django.contrib import admin

from .models import Device


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = (
        "device_model",
        "platform",
        "app_version",
        "status",
        "active_model_version",
        "active_map_version",
        "last_seen_at",
    )
    list_filter = ("platform", "status")
    search_fields = ("device_key", "device_model", "os_version", "app_version")
