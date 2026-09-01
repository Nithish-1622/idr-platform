from common.storage import StorageService

from .models import MapPackage


def register_map_package_service(
    name: str, region_code: str, version: str, file_obj, bbox: dict
) -> MapPackage:
    """Saves map package file artifact, computes SHA256 checksum, creates MapPackage record."""
    content = file_obj.read()
    storage_path, checksum, size_bytes = StorageService.save_artifact(
        f"maps/packages/{region_code}_{version}.mbtiles", content
    )

    package = MapPackage.objects.create(
        name=name,
        region_code=region_code,
        version=version,
        checksum_sha256=checksum,
        file_size_bytes=size_bytes,
        file_path=storage_path,
        min_latitude=bbox.get("min_lat", 0.0),
        max_latitude=bbox.get("max_lat", 0.0),
        min_longitude=bbox.get("min_lng", 0.0),
        max_longitude=bbox.get("max_lng", 0.0),
    )
    return package


def find_maps_for_coordinates(lat: float, lng: float) -> list:
    """Queries active map packages matching the given lat/lng coordinates."""
    return MapPackage.objects.filter(
        is_active=True,
        min_latitude__lte=lat,
        max_latitude__gte=lat,
        min_longitude__lte=lng,
        max_longitude__gte=lng,
    )
