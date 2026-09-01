from django.contrib import admin

from .models import UpdateManifest


@admin.register(UpdateManifest)
class UpdateManifestAdmin(admin.ModelAdmin):
    list_display = (
        "payload_type",
        "target_version",
        "target_platform",
        "checksum_sha256",
        "is_mandatory",
        "created_at",
    )
    list_filter = ("payload_type", "target_platform", "is_mandatory")
    search_fields = ("target_version", "checksum_sha256")
