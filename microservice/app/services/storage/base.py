"""Base storage service interface."""

from abc import ABC, abstractmethod
from typing import BinaryIO, Optional


class StorageService(ABC):
    """Abstract base class for storage services."""

    @abstractmethod
    def upload_bytes(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        """Upload bytes to storage.

        Args:
            key: Storage key/path
            data: Binary data to upload
            content_type: Optional MIME type

        Returns:
            URI of uploaded object (e.g., s3://bucket/key)
        """
        pass

    @abstractmethod
    def download_to_path(self, key: str, dest_path: str) -> None:
        """Download object to local file path.

        Args:
            key: Storage key/path
            dest_path: Local destination path
        """
        pass

    @abstractmethod
    def get_uri(self, key: str) -> str:
        """Get URI for a storage key.

        Args:
            key: Storage key/path

        Returns:
            Full URI (e.g., s3://bucket/key)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete object from storage.

        Args:
            key: Storage key/path
        """
        pass

