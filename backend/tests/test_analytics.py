import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_analytics_endpoints(auth_client):
    url_summary = reverse("analytics:summary")
    res_summary = auth_client.get(url_summary)
    assert res_summary.status_code == status.HTTP_200_OK
    assert "devices" in res_summary.data
    assert "telemetry" in res_summary.data

    url_perf = reverse("analytics:model_performance")
    res_perf = auth_client.get(url_perf)
    assert res_perf.status_code == status.HTTP_200_OK
    assert "usage_by_version" in res_perf.data
