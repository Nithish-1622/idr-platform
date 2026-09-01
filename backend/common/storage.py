import hashlib

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


class StorageService:
    """
    Abstract file storage helper for local filesystem and future object storage compatibility.
    Handles artifact storage, SHA256 checksum calculation, and file retrieval.
    """

    @staticmethod
    def save_artifact(file_path: str, content: bytes) -> tuple[str, str, int]:
        """
        Saves a binary file to storage.
        Returns tuple of (storage_path, sha256_checksum, size_in_bytes).
        """
        checksum = hashlib.sha256(content).hexdigest()
        size_bytes = len(content)
        saved_path = default_storage.save(file_path, ContentFile(content))
        return saved_path, checksum, size_bytes

    @staticmethod
    def calculate_checksum(file_field) -> str:
        """Calculates SHA256 checksum of an open file field or file path."""
        hasher = hashlib.sha256()
        for chunk in file_field.chunks():
            hasher.update(chunk)
        return hasher.hexdigest()
