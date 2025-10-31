"""Document management endpoints."""

import os
import time
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.dependencies import (
    get_document_processor_service,
    get_metadata_repository,
    get_storage_service,
    get_vectorizer_service,
)
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.schemas import (
    DocumentFormat,
    DocumentStatus,
    DocumentUploadResponse,
    ProcessDocumentRequest,
    ProcessDocumentResponse,
    VectorizeRequest,
    VectorizeResponse,
)
from app.repositories.metadata_store import MetadataRepository
from app.services.document_processor import DocumentProcessorService
from app.services.storage import StorageService
from app.services.vectorizer import VectorizerService

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
    storage: StorageService = Depends(get_storage_service),
) -> DocumentUploadResponse:
    """Upload a document (PDF, EPUB, or MOBI) to S3.

    Args:
        file: Document file to upload
        metadata_repo: Metadata repository dependency
        storage: Storage service dependency

    Returns:
        DocumentUploadResponse with document details

    Raises:
        HTTPException: If file format not supported or file too large
    """
    settings = get_settings()

    # Validate file format
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    if file_ext not in [fmt.value for fmt in DocumentFormat]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Supported: pdf, epub, mobi",
        )

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
        )

    logger.info(f"Uploading document: {file.filename} ({file_size} bytes)")

    try:
        import uuid

        # Generate unique file ID and S3 key
        file_id = str(uuid.uuid4())
        s3_key = f"{settings.s3_prefix}{file_id}_{file.filename}"

        # Read file content
        content = await file.read()

        # Upload to S3
        s3_uri = storage.upload_bytes(
            key=s3_key,
            data=content,
            content_type=file.content_type,
        )

        logger.info(f"Uploaded to S3: {s3_uri}")

        # Create document record in database with S3 URI
        document = metadata_repo.create_document(
            filename=file.filename,
            file_path=s3_uri,
            format=file_ext,
            file_size_bytes=file_size,
        )

        return DocumentUploadResponse(
            document_id=document.id,
            filename=document.filename,
            format=DocumentFormat(document.format),
            status=DocumentStatus(document.status),
            file_size_bytes=document.file_size_bytes,
            created_at=document.created_at,
        )

    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")


@router.post("/process", response_model=ProcessDocumentResponse)
async def process_document(
    request: ProcessDocumentRequest,
    doc_processor: DocumentProcessorService = Depends(get_document_processor_service),
) -> ProcessDocumentResponse:
    """Process a document: extract text and create chunks.

    Args:
        request: Processing request with document_id and chunking parameters
        doc_processor: Document processor service dependency

    Returns:
        ProcessDocumentResponse with processing results

    Raises:
        HTTPException: If document not found or processing fails
    """
    logger.info(f"Processing document: {request.document_id}")

    try:
        start_time = time.time()

        chunks = doc_processor.process_document(
            document_id=request.document_id,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
        )

        processing_time = time.time() - start_time

        return ProcessDocumentResponse(
            document_id=request.document_id,
            chunks_created=len(chunks),
            status=DocumentStatus.PROCESSED,
            processing_time_seconds=round(processing_time, 2),
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing document: {str(e)}")


@router.post("/vectorize", response_model=VectorizeResponse)
async def vectorize_document(
    request: VectorizeRequest,
    vectorizer: VectorizerService = Depends(get_vectorizer_service),
) -> VectorizeResponse:
    """Vectorize document chunks and store in pgvector.

    Args:
        request: Vectorization request with document_id
        vectorizer: Vectorizer service dependency

    Returns:
        VectorizeResponse with vectorization results

    Raises:
        HTTPException: If document not found or vectorization fails
    """
    logger.info(f"Vectorizing document: {request.document_id}")

    try:
        start_time = time.time()

        vectors_count = vectorizer.vectorize_document(request.document_id)

        processing_time = time.time() - start_time

        return VectorizeResponse(
            document_id=request.document_id,
            vectors_created=vectors_count,
            status=DocumentStatus.VECTORIZED,
            processing_time_seconds=round(processing_time, 2),
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error vectorizing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error vectorizing document: {str(e)}")


@router.get("/{document_id}", response_model=DocumentUploadResponse)
async def get_document(
    document_id: str,
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
) -> DocumentUploadResponse:
    """Get document information by ID.

    Args:
        document_id: Document identifier
        metadata_repo: Metadata repository dependency

    Returns:
        DocumentUploadResponse with document details

    Raises:
        HTTPException: If document not found
    """
    document = metadata_repo.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")

    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        format=DocumentFormat(document.format),
        status=DocumentStatus(document.status),
        file_size_bytes=document.file_size_bytes,
        created_at=document.created_at,
    )

