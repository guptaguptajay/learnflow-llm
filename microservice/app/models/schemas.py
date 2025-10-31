"""Pydantic V2 models for request/response validation."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class DocumentStatus(str, Enum):
    """Document processing status."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    VECTORIZED = "vectorized"
    MAPPED = "mapped"
    FAILED = "failed"


class DocumentFormat(str, Enum):
    """Supported document formats."""

    PDF = "pdf"
    EPUB = "epub"
    MOBI = "mobi"


# ============================================================================
# Document Upload Schemas
# ============================================================================


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""

    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    format: DocumentFormat = Field(..., description="Document format")
    status: DocumentStatus = Field(..., description="Current processing status")
    file_size_bytes: int = Field(..., description="File size in bytes")
    created_at: datetime = Field(..., description="Upload timestamp")

    model_config = {"from_attributes": True}


# ============================================================================
# Document Processing Schemas
# ============================================================================


class ProcessDocumentRequest(BaseModel):
    """Request to process a document."""

    document_id: str = Field(..., description="Document ID to process")
    chunk_size: Optional[int] = Field(default=1000, ge=100, le=10000, description="Chunk size")
    chunk_overlap: Optional[int] = Field(
        default=200, ge=0, le=1000, description="Overlap between chunks"
    )


class ProcessDocumentResponse(BaseModel):
    """Response after document processing."""

    document_id: str = Field(..., description="Document identifier")
    chunks_created: int = Field(..., description="Number of chunks created")
    status: DocumentStatus = Field(..., description="Processing status")
    processing_time_seconds: float = Field(..., description="Processing duration")


# ============================================================================
# Vectorization Schemas
# ============================================================================


class VectorizeRequest(BaseModel):
    """Request to vectorize document chunks."""

    document_id: str = Field(..., description="Document ID to vectorize")


class VectorizeResponse(BaseModel):
    """Response after vectorization."""

    document_id: str = Field(..., description="Document identifier")
    vectors_created: int = Field(..., description="Number of vectors created")
    status: DocumentStatus = Field(..., description="Vectorization status")
    processing_time_seconds: float = Field(..., description="Processing duration")


# ============================================================================
# Mind Map / Topic Schemas
# ============================================================================


class TopicNode(BaseModel):
    """Represents a topic or subtopic in the mind map."""

    id: str = Field(..., description="Unique topic identifier")
    document_id: str = Field(..., description="Parent document ID")
    title: str = Field(..., description="Topic title")
    level: int = Field(..., description="Hierarchy level (0=root, 1=topic, 2=subtopic)")
    parent_id: Optional[str] = Field(None, description="Parent topic ID")
    summary: Optional[str] = Field(None, description="Topic summary")
    vector_ids: List[str] = Field(default_factory=list, description="Associated vector IDs")
    chunk_ids: List[str] = Field(default_factory=list, description="Associated chunk IDs")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {"from_attributes": True}


class GenerateTopicsRequest(BaseModel):
    """Request to generate main topics from document."""

    document_id: str = Field(..., description="Document ID")
    num_topics: Optional[int] = Field(
        default=5, ge=1, le=50, description="Number of topics to generate"
    )


class GenerateTopicsResponse(BaseModel):
    """Response with generated topics."""

    document_id: str = Field(..., description="Document identifier")
    topics: List[TopicNode] = Field(..., description="Generated topics")
    processing_time_seconds: float = Field(..., description="Processing duration")


class GenerateSubtopicsRequest(BaseModel):
    """Request to generate subtopics for a topic."""

    topic_id: str = Field(..., description="Parent topic ID")
    num_subtopics: Optional[int] = Field(
        default=5, ge=1, le=20, description="Number of subtopics to generate"
    )


class GenerateSubtopicsResponse(BaseModel):
    """Response with generated subtopics."""

    topic_id: str = Field(..., description="Parent topic ID")
    subtopics: List[TopicNode] = Field(..., description="Generated subtopics")
    processing_time_seconds: float = Field(..., description="Processing duration")


# ============================================================================
# Summary Schemas
# ============================================================================


class GenerateSummaryRequest(BaseModel):
    """Request to generate summary for topic/subtopic."""

    topic_id: str = Field(..., description="Topic or subtopic ID")

    @field_validator("topic_id")
    @classmethod
    def validate_topic_id(cls, v: str) -> str:
        """Validate topic ID is not empty."""
        if not v or not v.strip():
            raise ValueError("topic_id cannot be empty")
        return v.strip()


class GenerateSummaryResponse(BaseModel):
    """Response with generated summary."""

    topic_id: str = Field(..., description="Topic identifier")
    summary: str = Field(..., description="Generated summary text")
    processing_time_seconds: float = Field(..., description="Processing duration")


# ============================================================================
# Content Retrieval Schemas
# ============================================================================


class GetContentRequest(BaseModel):
    """Request to get full content for topic/subtopic."""

    topic_id: str = Field(..., description="Topic or subtopic ID")


class GetContentResponse(BaseModel):
    """Response with full content."""

    topic_id: str = Field(..., description="Topic identifier")
    title: str = Field(..., description="Topic title")
    full_text: str = Field(..., description="Complete text from all associated chunks")
    chunk_ids: List[str] = Field(..., description="Source chunk IDs")
    chunk_count: int = Field(..., description="Number of chunks")


# ============================================================================
# Health Check Schemas
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    database: str = Field(..., description="Database connection status")
    vector_store: str = Field(..., description="Vector store connection status")


# ============================================================================
# Error Response Schema
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")

