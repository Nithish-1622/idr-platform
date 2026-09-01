import pytest
from django.urls import reverse
from rest_framework import status

from apps.models.models import MLModel, ModelVersion
from apps.models.services import (
    approve_model_version_service,
    publish_model_version_service,
)


@pytest.mark.django_db
def test_ml_model_lifecycle(auth_client):
    # 1. Create Model
    ml_model = MLModel.objects.create(
        name="IDR_LSTM_V1",
        model_type="IDR_RECURRENT",
        description="LSTM based dead reckoning model",
    )

    # 2. Create Model Version
    version = ModelVersion.objects.create(
        ml_model=ml_model,
        semantic_version="1.0.0",
        status=ModelVersion.Status.DRAFT,
        min_app_version="1.0.0",
        supported_platforms=["ANDROID", "IOS"],
    )
    assert version.status == ModelVersion.Status.DRAFT

    # 3. Approve Model Version
    approved_ver = approve_model_version_service(version)
    assert approved_ver.status == ModelVersion.Status.APPROVED

    # 4. Publish Model Version
    deployment = publish_model_version_service(approved_ver, target_platform="ANDROID")
    assert deployment.is_active is True
    approved_ver.refresh_from_db()
    assert approved_ver.status == ModelVersion.Status.ACTIVE


@pytest.mark.django_db
def test_latest_active_model_api(api_client):
    ml_model = MLModel.objects.create(
        name="IDR_TRANSFORMER", model_type="IDR_TRANSFORMER"
    )
    version = ModelVersion.objects.create(
        ml_model=ml_model, semantic_version="2.0.0", status=ModelVersion.Status.APPROVED
    )
    publish_model_version_service(version, target_platform="ALL")

    url = reverse("models:latest")
    response = api_client.get(url, {"platform": "ANDROID"})
    assert response.status_code == status.HTTP_200_OK
    assert response.data["semantic_version"] == "2.0.0"
