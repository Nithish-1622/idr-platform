import pytest
from django.urls import reverse
from rest_framework import status

from apps.maps.models import MapPackage


@pytest.mark.django_db
def test_map_package_list_and_lookup(api_client):
    package = MapPackage.objects.create(
        name="Bengaluru Central Map",
        region_code="IND-KA-BLR",
        version="2026.01",
        checksum_sha256="a" * 64,
        file_size_bytes=1048576,
        min_latitude=12.90,
        max_latitude=13.00,
        min_longitude=77.50,
        max_longitude=77.65,
        is_active=True,
    )

    url_list = reverse("maps:list")
    res_list = api_client.get(url_list)
    assert res_list.status_code == status.HTTP_200_OK
    assert len(res_list.data) == 1

    url_lookup = reverse("maps:lookup")
    res_lookup = api_client.get(url_lookup, {"lat": 12.95, "lng": 77.55})
    assert res_lookup.status_code == status.HTTP_200_OK
    assert len(res_lookup.data) == 1
    assert res_lookup.data[0]["region_code"] == "IND-KA-BLR"
