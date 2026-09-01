import logging

from celery import shared_task

from common.storage import StorageService

from .models import ModelArtifact

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def verify_model_artifact_checksum_task(self, artifact_id: str):
    """Celery task to verify binary artifact SHA256 checksum in background."""
    try:
        artifact = ModelArtifact.objects.get(id=artifact_id)
        if artifact.file_path:
            computed_checksum = StorageService.calculate_checksum(artifact.file_path)
            if computed_checksum != artifact.checksum_sha256:
                logger.error(
                    f"Checksum mismatch for artifact {artifact_id}! Expected {artifact.checksum_sha256}, got {computed_checksum}"
                )
                return False
            logger.info(f"Artifact {artifact_id} checksum verified successfully.")
            return True
    except Exception as exc:
        logger.error(f"Error in verify_model_artifact_checksum_task: {exc}")
        raise self.retry(exc=exc, countdown=10)
