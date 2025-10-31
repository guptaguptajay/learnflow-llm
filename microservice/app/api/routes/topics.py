"""Topic and mind map endpoints."""

import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import (
    get_metadata_repository,
    get_mindmap_generator_service,
    get_summarizer_service,
)
from app.core.logging import get_logger
from app.models.schemas import (
    GenerateSubtopicsRequest,
    GenerateSubtopicsResponse,
    GenerateSummaryRequest,
    GenerateSummaryResponse,
    GenerateTopicsRequest,
    GenerateTopicsResponse,
    GetContentRequest,
    GetContentResponse,
    TopicNode,
)
from app.repositories.metadata_store import MetadataRepository
from app.services.mindmap_generator import MindMapGeneratorService
from app.services.summarizer import SummarizerService

logger = get_logger(__name__)
router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("/generate", response_model=GenerateTopicsResponse)
async def generate_topics(
    request: GenerateTopicsRequest,
    mindmap_service: MindMapGeneratorService = Depends(get_mindmap_generator_service),
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
) -> GenerateTopicsResponse:
    """Generate main topics for a document.

    Args:
        request: Topic generation request
        mindmap_service: Mind map generator service dependency
        metadata_repo: Metadata repository dependency

    Returns:
        GenerateTopicsResponse with generated topics

    Raises:
        HTTPException: If document not found or generation fails
    """
    logger.info(f"Generating topics for document: {request.document_id}")

    try:
        start_time = time.time()

        topic_nodes = mindmap_service.generate_topics(
            document_id=request.document_id, num_topics=request.num_topics
        )

        # Convert to response format with vector_ids and chunk_ids
        topics_response = []
        for node in topic_nodes:
            vector_ids = metadata_repo.get_vector_ids_by_topic(node.id)
            chunks = metadata_repo.get_chunks_by_topic(node.id)
            chunk_ids = [chunk.id for chunk in chunks]

            topics_response.append(
                TopicNode(
                    id=node.id,
                    document_id=node.document_id,
                    title=node.title,
                    level=node.level,
                    parent_id=node.parent_id,
                    summary=node.summary,
                    vector_ids=vector_ids,
                    chunk_ids=chunk_ids,
                    created_at=node.created_at,
                )
            )

        processing_time = time.time() - start_time

        return GenerateTopicsResponse(
            document_id=request.document_id,
            topics=topics_response,
            processing_time_seconds=round(processing_time, 2),
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating topics: {str(e)}")


@router.post("/subtopics/generate", response_model=GenerateSubtopicsResponse)
async def generate_subtopics(
    request: GenerateSubtopicsRequest,
    mindmap_service: MindMapGeneratorService = Depends(get_mindmap_generator_service),
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
    summarizer: SummarizerService = Depends(get_summarizer_service),
) -> GenerateSubtopicsResponse:
    """Generate subtopics for a parent topic.

    Args:
        request: Subtopic generation request
        mindmap_service: Mind map generator service dependency
        metadata_repo: Metadata repository dependency

    Returns:
        GenerateSubtopicsResponse with generated subtopics

    Raises:
        HTTPException: If topic not found or generation fails
    """
    logger.info(f"Generating subtopics for topic: {request.topic_id}")

    try:
        start_time = time.time()

        subtopic_nodes = mindmap_service.generate_subtopics(
            topic_id=request.topic_id, num_subtopics=request.num_subtopics
        )

        # Convert to response format
        subtopics_response = []
        for node in subtopic_nodes:
            # Generate and persist summary for each subtopic
            try:
                summary_text = summarizer.generate_summary_for_topic(node.id)
            except Exception:
                summary_text = None
            vector_ids = metadata_repo.get_vector_ids_by_topic(node.id)
            chunks = metadata_repo.get_chunks_by_topic(node.id)
            chunk_ids = [chunk.id for chunk in chunks]

            subtopics_response.append(
                TopicNode(
                    id=node.id,
                    document_id=node.document_id,
                    title=node.title,
                    level=node.level,
                    parent_id=node.parent_id,
                    summary=summary_text or node.summary,
                    vector_ids=vector_ids,
                    chunk_ids=chunk_ids,
                    created_at=node.created_at,
                )
            )

        processing_time = time.time() - start_time

        return GenerateSubtopicsResponse(
            topic_id=request.topic_id,
            subtopics=subtopics_response,
            processing_time_seconds=round(processing_time, 2),
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating subtopics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating subtopics: {str(e)}")


@router.post("/summary/generate", response_model=GenerateSummaryResponse)
async def generate_summary(
    request: GenerateSummaryRequest,
    summarizer: SummarizerService = Depends(get_summarizer_service),
) -> GenerateSummaryResponse:
    """Generate summary for a topic or subtopic.

    Args:
        request: Summary generation request
        summarizer: Summarizer service dependency

    Returns:
        GenerateSummaryResponse with generated summary

    Raises:
        HTTPException: If topic not found or generation fails
    """
    logger.info(f"Generating summary for topic: {request.topic_id}")

    try:
        start_time = time.time()

        summary = summarizer.generate_summary_for_topic(request.topic_id)

        processing_time = time.time() - start_time

        return GenerateSummaryResponse(
            topic_id=request.topic_id,
            summary=summary,
            processing_time_seconds=round(processing_time, 2),
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@router.post("/content", response_model=GetContentResponse)
async def get_topic_content(
    request: GetContentRequest,
    summarizer: SummarizerService = Depends(get_summarizer_service),
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
) -> GetContentResponse:
    """Get full content for a topic or subtopic.

    Args:
        request: Content request
        summarizer: Summarizer service dependency
        metadata_repo: Metadata repository dependency

    Returns:
        GetContentResponse with full text and chunk information

    Raises:
        HTTPException: If topic not found
    """
    logger.info(f"Getting content for topic: {request.topic_id}")

    try:
        # Get topic
        topic = metadata_repo.get_topic_by_id(request.topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail=f"Topic not found: {request.topic_id}")

        # Get full content
        full_text, chunk_ids = summarizer.get_topic_content(request.topic_id)

        return GetContentResponse(
            topic_id=request.topic_id,
            title=topic.title,
            full_text=full_text,
            chunk_ids=chunk_ids,
            chunk_count=len(chunk_ids),
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting content: {str(e)}")


@router.get("/{document_id}", response_model=List[TopicNode])
async def get_document_topics(
    document_id: str,
    level: Optional[int] = None,
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
) -> List[TopicNode]:
    """Get all topics for a document, optionally filtered by level.

    Args:
        document_id: Document identifier
        level: Optional level filter (1=topics, 2=subtopics, etc.)
        metadata_repo: Metadata repository dependency

    Returns:
        List of TopicNode instances

    Raises:
        HTTPException: If document not found
    """
    logger.info(f"Getting topics for document: {document_id}")

    try:
        # Check if document exists
        document = metadata_repo.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")

        # Get topics
        topics = metadata_repo.get_topics_by_document(document_id, level=level)

        # Convert to response format
        topics_response = []
        for node in topics:
            vector_ids = metadata_repo.get_vector_ids_by_topic(node.id)
            chunks = metadata_repo.get_chunks_by_topic(node.id)
            chunk_ids = [chunk.id for chunk in chunks]

            topics_response.append(
                TopicNode(
                    id=node.id,
                    document_id=node.document_id,
                    title=node.title,
                    level=node.level,
                    parent_id=node.parent_id,
                    summary=node.summary,
                    vector_ids=vector_ids,
                    chunk_ids=chunk_ids,
                    created_at=node.created_at,
                )
            )

        return topics_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting topics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting topics: {str(e)}")

