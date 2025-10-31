"""PostgreSQL pgvector store repository."""

import time
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Integer, String, Text, create_engine, text, Index, bindparam
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from pgvector.sqlalchemy import Vector

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ============================================================================
# SQLAlchemy Model for Embeddings
# ============================================================================


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""

    pass


class Embedding(Base):
    """Embedding model for pgvector storage."""

    __tablename__ = "embeddings"

    chunk_id = Column(String, primary_key=True)
    document_id = Column(String, nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(3072), nullable=False)
    payload = Column(JSONB, nullable=True)

    __table_args__ = (
        Index("idx_embeddings_doc", "document_id"),
        Index("idx_embeddings_doc_chunk", "document_id", "chunk_index"),
    )


# ============================================================================
# Repository Class
# ============================================================================


class ScoredPoint:
    """Mock ScoredPoint to match Qdrant's interface."""

    def __init__(self, id: str, score: float, payload: Optional[Dict[str, Any]] = None):
        self.id = id
        self.score = score
        self.payload = payload or {}


class VectorStoreRepository:
    """Repository for vector operations using PostgreSQL pgvector."""

    def __init__(
        self,
        database_url: Optional[str] = None,
    ):
        """Initialize pgvector store repository.

        Args:
            database_url: PostgreSQL connection URL. If None, uses settings.
        """
        settings = get_settings()
        self.database_url = database_url or settings.database_url
        self.dimension = settings.pgvector_dimension
        self.ivfflat_lists = settings.pgvector_ivfflat_lists

        self.engine = create_engine(
            self.database_url, echo=settings.debug, pool_pre_ping=True
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine, expire_on_commit=False
        )
        logger.info(f"Initialized pgvector client with dimension={self.dimension}")

        # Ensure extension and table exist
        self._ensure_extension()
        self._ensure_table()

    def _ensure_extension(self) -> None:
        """Ensure pgvector extension is enabled."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("pgvector extension enabled")
        except Exception as e:
            logger.warning(f"Could not enable pgvector extension: {str(e)}")

    def _ensure_table(self) -> None:
        """Ensure embeddings table exists."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Embeddings table ensured")
        except Exception as e:
            logger.error(f"Error creating embeddings table: {str(e)}")
            raise

    def _ensure_ivfflat_index(self) -> None:
        """Ensure IVFFlat index exists for vector similarity search."""
        try:
            with self.engine.connect() as conn:
                # Check if index exists
                result = conn.execute(
                    text(
                        """
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = 'embeddings' 
                    AND indexname = 'idx_embeddings_embedding_cosine'
                    """
                    )
                )
                if result.fetchone():
                    logger.debug("IVFFlat index already exists")
                    return

                # Create IVFFlat index for cosine distance
                conn.execute(
                    text(
                        f"""
                    CREATE INDEX IF NOT EXISTS idx_embeddings_embedding_cosine 
                    ON embeddings USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = {self.ivfflat_lists})
                    """
                    )
                )
                conn.commit()
                logger.info(
                    f"Created IVFFlat index with lists={self.ivfflat_lists}"
                )
        except Exception as e:
            logger.warning(f"Could not create IVFFlat index: {str(e)}")

    def _retry_operation(self, operation, max_retries: int = 3, delay: float = 1.0):
        """Retry operation with exponential backoff.

        Args:
            operation: Callable operation to retry
            max_retries: Maximum number of retries
            delay: Initial delay between retries

        Returns:
            Operation result

        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                return operation()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(
                    f"Operation failed (attempt {attempt + 1}/{max_retries}): {str(e)}"
                )
                time.sleep(delay * (2**attempt))

    def create_collection(
        self, collection_name: str, vector_size: int, distance: str = "Cosine"
    ) -> bool:
        """Create a collection (ensure table and indexes exist).

        Args:
            collection_name: Name of the collection (used for document_id filter)
            vector_size: Dimension of vectors (must match pgvector_dimension)
            distance: Distance metric (Cosine supported)

        Returns:
            True if created successfully
        """
        if vector_size != self.dimension:
            logger.warning(
                f"Vector size {vector_size} doesn't match configured dimension {self.dimension}"
            )

        # Ensure table exists
        self._ensure_table()

        # Ensure IVFFlat index exists
        self._ensure_ivfflat_index()

        logger.info(f"Collection {collection_name} ready (using embeddings table)")
        return True

    def collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists (table exists).

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(
                        "SELECT 1 FROM information_schema.tables WHERE table_name = 'embeddings'"
                    )
                )
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking collection existence: {str(e)}")
            return False

    def insert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """Insert vectors with metadata into collection.

        Args:
            collection_name: Name of the collection (used to set document_id)
            vectors: List of vector embeddings
            metadata: List of metadata dictionaries
            ids: Optional list of IDs. If None, auto-generated.

        Returns:
            List of vector IDs
        """

        def _insert():
            if ids:
                vector_ids = ids
            else:
                # Generate UUIDs for vectors
                import uuid

                vector_ids = [str(uuid.uuid4()) for _ in range(len(vectors))]

            with self.SessionLocal() as session:
                embeddings = []
                for vid, vector, meta in zip(vector_ids, vectors, metadata):
                    # Extract document_id from metadata or use collection_name
                    document_id = meta.get("document_id", collection_name.split("_")[-1])
                    chunk_index = meta.get("chunk_index", 0)

                    embedding = Embedding(
                        chunk_id=vid,
                        document_id=document_id,
                        chunk_index=chunk_index,
                        embedding=vector,
                        payload=meta,
                    )
                    embeddings.append(embedding)

                # Bulk insert
                batch_size = 100
                for i in range(0, len(embeddings), batch_size):
                    batch = embeddings[i : i + batch_size]
                    session.bulk_save_objects(batch)
                    logger.debug(
                        f"Inserted batch {i // batch_size + 1} of {len(batch)} vectors"
                    )

                session.commit()
                logger.info(f"Inserted {len(vectors)} vectors into {collection_name}")

            return vector_ids

        return self._retry_operation(_insert)

    def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[ScoredPoint]:
        """Search for similar vectors using cosine distance.

        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Metadata filter conditions

        Returns:
            List of scored points
        """

        def _search():
            with self.SessionLocal() as session:
                # Extract document_id from collection_name
                document_id = collection_name.split("_")[-1]

                # Build query with cosine distance
                # <=> operator is cosine distance (0 = identical, 2 = opposite)
                # Convert to similarity score: 1 - (distance / 2)
                query = (
                    text(
                        """
                        SELECT chunk_id, payload, 
                               (1 - (embedding <=> :query_vector) / 2) as score
                        FROM embeddings
                        WHERE document_id = :document_id
                        ORDER BY embedding <=> :query_vector
                        LIMIT :limit
                        """
                    )
                    .bindparams(bindparam("query_vector", type_=Vector(self.dimension)))
                )

                result = session.execute(
                    query,
                    {
                        "query_vector": query_vector,
                        "document_id": document_id,
                        "limit": limit,
                    },
                )

                rows = result.fetchall()

                # Filter by score threshold if provided
                scored_points = []
                for row in rows:
                    chunk_id, payload, score = row
                    if score_threshold is None or score >= score_threshold:
                        scored_points.append(
                            ScoredPoint(id=chunk_id, score=score, payload=payload)
                        )

                logger.debug(f"Search returned {len(scored_points)} results")
                return scored_points

        return self._retry_operation(_search)

    def get_vectors_by_ids(
        self, collection_name: str, ids: List[str]
    ) -> List[Any]:
        """Retrieve vectors by IDs.

        Args:
            collection_name: Name of the collection
            ids: List of vector IDs

        Returns:
            List of records
        """

        def _retrieve():
            with self.SessionLocal() as session:
                embeddings = (
                    session.query(Embedding).filter(Embedding.chunk_id.in_(ids)).all()
                )
                logger.debug(f"Retrieved {len(embeddings)} vectors")
                return embeddings

        return self._retry_operation(_retrieve)

    def delete_vectors(self, collection_name: str, ids: List[str]) -> bool:
        """Delete vectors by IDs.

        Args:
            collection_name: Name of the collection
            ids: List of vector IDs to delete

        Returns:
            True if deleted successfully
        """

        def _delete():
            with self.SessionLocal() as session:
                session.query(Embedding).filter(Embedding.chunk_id.in_(ids)).delete(
                    synchronize_session=False
                )
                session.commit()
                logger.info(f"Deleted {len(ids)} vectors from {collection_name}")
                return True

        return self._retry_operation(_delete)

    def delete_collection(self, collection_name: str) -> bool:
        """Delete entire collection (all vectors for a document).

        Args:
            collection_name: Name of the collection

        Returns:
            True if deleted successfully
        """

        def _delete():
            # Extract document_id from collection_name
            document_id = collection_name.split("_")[-1]

            with self.SessionLocal() as session:
                session.query(Embedding).filter(
                    Embedding.document_id == document_id
                ).delete(synchronize_session=False)
                session.commit()
                logger.info(f"Deleted collection: {collection_name}")
                return True

        return self._retry_operation(_delete)

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        """Get collection information.

        Args:
            collection_name: Name of the collection

        Returns:
            Collection info dictionary or None
        """
        try:
            document_id = collection_name.split("_")[-1]

            with self.SessionLocal() as session:
                count = (
                    session.query(Embedding)
                    .filter(Embedding.document_id == document_id)
                    .count()
                )

                return {
                    "name": collection_name,
                    "vectors_count": count,
                    "points_count": count,
                    "status": "green" if count > 0 else "yellow",
                }
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            return None

    def health_check(self) -> bool:
        """Check if pgvector is healthy.

        Returns:
            True if healthy
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.debug("pgvector health check passed")
                return True
        except Exception as e:
            logger.error(f"pgvector health check failed: {str(e)}")
            return False

