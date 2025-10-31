"""Main FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, health, topics
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.repositories.metadata_store import MetadataRepository

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events.

    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info("Starting GenAI Document Mapping Service")
    settings = get_settings()

    # Initialize database tables
    try:
        metadata_repo = MetadataRepository()
        metadata_repo.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

    # Create upload directories
    import os

    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.temp_dir, exist_ok=True)
    logger.info(f"Upload directory: {settings.upload_dir}")
    logger.info(f"Temp directory: {settings.temp_dir}")

    yield

    # Shutdown
    logger.info("Shutting down GenAI Document Mapping Service")


# Initialize FastAPI app
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Senior-level GenAI microservice for document processing and knowledge mapping",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(topics.router)


@app.get("/")
async def root():
    """Root endpoint with API information.

    Returns:
        Dictionary with API information
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )

