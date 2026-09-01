from rest_framework import serializers

from .models import MapPackage, MapRegion


class MapPackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapPackage
        fields = [
            "id",
            "name",
            "region_code",
            "version",
            "checksum_sha256",
            "file_size_bytes",
            "file_path",
            "min_latitude",
            "max_latitude",
            "min_longitude",
            "max_longitude",
            "is_active",
            "compatibility_min_app_version",
            "created_at",
        ]
        read_only_fields = ["id", "checksum_sha256", "file_size_bytes", "created_at"]


class MapRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapRegion
        fields = ["id", "code", "name", "country_code", "bounding_box"]
