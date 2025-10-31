"""Local filesystem storage service implementation."""

import os
import shutil
from typing import Optional

from app.core.logging import get_logger
from app.services.storage.base import StorageService

logger = get_logger(__name__)


class LocalStorageService(StorageService):
    """Local filesystem-backed storage service.

    Objects are stored under a configured base directory, preserving any
    provided key path structure (e.g., "documents/abc/file.pdf").
    """

    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Initialized Local storage: base_dir={self.base_dir}")

    def _resolve_path(self, key: str) -> str:
        # Normalize and prevent path traversal outside base_dir
        normalized = os.path.normpath(key).lstrip(os.sep)
        full_path = os.path.join(self.base_dir, normalized)
        if not os.path.abspath(full_path).startswith(self.base_dir + os.sep):
            raise ValueError("Invalid storage key; path traversal detected")
        return full_path

    def upload_bytes(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        dest_path = self._resolve_path(key)
        os.makedirs(os.path.dirname(dest_path) or self.base_dir, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)
        uri = self.get_uri(key)
        logger.info(f"Saved to Local storage: {uri} ({len(data)} bytes)")
        return uri

    def download_to_path(self, key: str, dest_path: str) -> None:
        src_path = self._resolve_path(key)
        os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)
        shutil.copyfile(src_path, dest_path)
        logger.info(f"Downloaded from Local storage: {src_path} -> {dest_path}")

    def get_uri(self, key: str) -> str:
        full_path = self._resolve_path(key)
        return f"file://{full_path}"

    def delete(self, key: str) -> None:
        path = self._resolve_path(key)
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"Deleted from Local storage: {path}")
        else:
            logger.info(f"Local storage delete noop; not found: {path}")


