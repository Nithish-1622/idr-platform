from django.contrib import admin

from .models import MapPackage, MapRegion


@admin.register(MapPackage)
class MapPackageAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "region_code",
        "version",
        "checksum_sha256",
        "is_active",
        "created_at",
    )
    list_filter = ("region_code", "is_active")
    search_fields = ("name", "region_code", "version")


@admin.register(MapRegion)
class MapRegionAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "country_code")
    search_fields = ("name", "code", "country_code")
