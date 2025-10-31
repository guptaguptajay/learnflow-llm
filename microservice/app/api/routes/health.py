"""Health check endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_metadata_repository, get_vector_repository
from app.core.config import get_settings
from app.models.schemas import HealthCheckResponse
from app.repositories.metadata_store import MetadataRepository
from app.repositories.vector_store import VectorStoreRepository

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    metadata_repo: MetadataRepository = Depends(get_metadata_repository),
    vector_repo: VectorStoreRepository = Depends(get_vector_repository),
) -> HealthCheckResponse:
    """Check health of all services.

    Returns:
        HealthCheckResponse with status of each component
    """
    settings = get_settings()

    # Check database connection
    db_status = "healthy"
    try:
        with metadata_repo.get_session() as session:
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Check vector store connection
    vector_status = "healthy" if vector_repo.health_check() else "unhealthy"

    overall_status = "healthy" if db_status == "healthy" and vector_status == "healthy" else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version=settings.app_version,
        database=db_status,
        vector_store=vector_status,
    )

