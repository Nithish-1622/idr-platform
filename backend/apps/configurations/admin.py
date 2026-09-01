from django.contrib import admin

from .models import DeviceConfiguration, SystemConfiguration


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ("key", "is_active", "updated_at")
    search_fields = ("key", "description")


@admin.register(DeviceConfiguration)
class DeviceConfigurationAdmin(admin.ModelAdmin):
    list_display = ("device", "key", "updated_at")
    search_fields = ("key", "device__device_key")
