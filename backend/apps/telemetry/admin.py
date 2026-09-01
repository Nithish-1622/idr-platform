from django.contrib import admin

from .models import TelemetryBatch, TelemetryPoint, TelemetrySession


class TelemetryBatchInline(admin.TabularInline):
    model = TelemetryBatch
    extra = 0


@admin.register(TelemetrySession)
class TelemetrySessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "device", "total_points", "start_time", "end_time")
    search_fields = ("session_id", "device__device_key")
    inlines = [TelemetryBatchInline]


@admin.register(TelemetryPoint)
class TelemetryPointAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "session",
        "latitude",
        "longitude",
        "navigation_mode",
        "confidence",
    )
    list_filter = ("navigation_mode", "gnss_status")
    search_fields = ("session__session_id",)
