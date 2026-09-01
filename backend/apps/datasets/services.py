from common.storage import StorageService

from .models import Dataset, DatasetVersion


def create_dataset_version_service(
    dataset: Dataset, version_str: str, file_obj, metadata: dict
) -> DatasetVersion:
    """Saves uploaded dataset binary, computes SHA256 checksum, creates DatasetVersion object."""
    content = file_obj.read()
    storage_path, checksum, size_bytes = StorageService.save_artifact(
        f"datasets/{dataset.name}_{version_str}.bin", content
    )

    dataset_version = DatasetVersion.objects.create(
        dataset=dataset,
        version=version_str,
        checksum_sha256=checksum,
        file_size_bytes=size_bytes,
        file_path=storage_path,
        metadata=metadata,
    )
    return dataset_version
