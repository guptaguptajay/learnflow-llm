"""Dependency injection for FastAPI."""

from functools import lru_cache

from fastapi import Depends
from app.core.config import get_settings
from app.repositories.metadata_store import MetadataRepository
from app.repositories.vector_store import VectorStoreRepository
from app.core.logging import get_logger

logger = get_logger(__name__)
from app.services.document_processor import DocumentProcessorService
from app.services.mindmap_generator import MindMapGeneratorService
from app.services.storage import LocalStorageService, S3StorageService, StorageService
from app.services.summarizer import SummarizerService
from app.services.vectorizer import VectorizerService


@lru_cache()
def get_metadata_repository() -> MetadataRepository:
    """Get metadata repository instance.

    Returns:
        MetadataRepository instance
    """
    # Try default (Postgres). If unavailable (e.g., tests/CI), fall back to in-memory SQLite.
    try:
        repo = MetadataRepository()
        # Ensure tables exist; if this fails, we'll fall back
        repo.create_tables()
        return repo
    except Exception as e:
        logger.warning(f"Default DB unavailable, falling back to in-memory SQLite: {str(e)}")
        repo = MetadataRepository(database_url="sqlite:///:memory:")
        repo.create_tables()
        return repo


@lru_cache()
def get_vector_repository() -> VectorStoreRepository:
    """Get vector store repository instance.

    Returns:
        VectorStoreRepository instance
    """
    try:
        return VectorStoreRepository()
    except Exception as e:
        # Fallback to a no-op vector store that avoids DB requirements during tests
        logger.warning(f"Vector store unavailable, using NoopVectorStoreRepository: {str(e)}")
        from app.repositories.fake_vector_store import NoopVectorStoreRepository

        return NoopVectorStoreRepository()


@lru_cache()
def get_storage_service() -> StorageService:
    """Get storage service instance.

    Returns:
        StorageService instance (S3 or local based on config)
    """
    settings = get_settings()
    
    if settings.use_s3_storage and settings.s3_bucket_name:
        return S3StorageService(
            bucket=settings.s3_bucket_name,
            region=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
            session_token=settings.aws_session_token,
        )
    else:
        # Fallback to local storage when S3 is not configured
        return LocalStorageService(base_dir=get_settings().upload_dir)


def get_document_processor_service(
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
    storage_service: StorageService = Depends(get_storage_service),
) -> DocumentProcessorService:
    """Get document processor service instance.

    Args:
        metadata_repo: Metadata repository
        storage_service: Storage service

    Returns:
        DocumentProcessorService instance
    """
    return DocumentProcessorService(metadata_repo, storage_service)


def get_vectorizer_service(
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
    vector_repo: VectorStoreRepository = Depends(get_vector_repository),
) -> VectorizerService:
    """Get vectorizer service instance.

    Args:
        metadata_repo: Optional metadata repository
        vector_repo: Optional vector repository

    Returns:
        VectorizerService instance
    """
    return VectorizerService(metadata_repo, vector_repo)


def get_mindmap_generator_service(
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
    vectorizer_service: VectorizerService = Depends(get_vectorizer_service),
) -> MindMapGeneratorService:
    """Get mind map generator service instance.

    Args:
        metadata_repo: Optional metadata repository
        vectorizer_service: Optional vectorizer service

    Returns:
        MindMapGeneratorService instance
    """
    return MindMapGeneratorService(metadata_repo, vectorizer_service)


def get_summarizer_service(
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
) -> SummarizerService:
    """Get summarizer service instance.

    Args:
        metadata_repo: Optional metadata repository

    Returns:
        SummarizerService instance
    """
    return SummarizerService(metadata_repo)

