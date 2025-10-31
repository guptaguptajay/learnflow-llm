"""Database initialization script."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.repositories.metadata_store import MetadataRepository

setup_logging()
logger = get_logger(__name__)


def main():
    """Initialize database tables."""
    logger.info("Initializing database...")

    settings = get_settings()
    logger.info(f"Database URL: {settings.database_url}")

    try:
        repo = MetadataRepository()
        repo.create_tables()
        logger.info("Database tables created successfully!")

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

