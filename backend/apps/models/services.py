from django.db import transaction
from django.utils import timezone

from common.storage import StorageService

from .models import Deployment, MLModel, ModelArtifact, ModelVersion


def create_model_version_with_artifact(
    ml_model: MLModel, semantic_version: str, file_obj, version_data: dict
) -> ModelVersion:
    """Creates a new model version and attaches ONNX artifact with SHA256 checksum."""
    with transaction.atomic():
        model_version = ModelVersion.objects.create(
            ml_model=ml_model,
            semantic_version=semantic_version,
            status=ModelVersion.Status.DRAFT,
            **version_data,
        )

        content = file_obj.read()
        saved_path, checksum, size_bytes = StorageService.save_artifact(
            f"models/onnx/{ml_model.name}_{semantic_version}.onnx", content
        )

        ModelArtifact.objects.create(
            model_version=model_version,
            format="ONNX",
            file_path=saved_path,
            checksum_sha256=checksum,
            file_size_bytes=size_bytes,
        )

        return model_version


def approve_model_version_service(model_version: ModelVersion) -> ModelVersion:
    """Transitions model status from DRAFT/VALIDATING to APPROVED."""
    if model_version.status not in [
        ModelVersion.Status.DRAFT,
        ModelVersion.Status.VALIDATING,
    ]:
        raise ValueError(
            f"Cannot approve model version in state {model_version.status}"
        )

    model_version.status = ModelVersion.Status.APPROVED
    model_version.save(update_fields=["status"])
    return model_version


def publish_model_version_service(
    model_version: ModelVersion, target_platform: str = "ALL"
) -> Deployment:
    """
    Atomically publishes an APPROVED model version, setting it to ACTIVE
    and creating a Deployment record.
    """
    if model_version.status != ModelVersion.Status.APPROVED:
        raise ValueError("Only APPROVED model versions can be published.")

    with transaction.atomic():
        # Deactivate existing deployments for target platform
        Deployment.objects.filter(
            model_version__ml_model=model_version.ml_model,
            target_platform=target_platform,
        ).update(is_active=False)

        model_version.status = ModelVersion.Status.ACTIVE
        model_version.release_date = timezone.now()
        model_version.save(update_fields=["status", "release_date"])

        deployment = Deployment.objects.create(
            model_version=model_version, target_platform=target_platform, is_active=True
        )
        return deployment
