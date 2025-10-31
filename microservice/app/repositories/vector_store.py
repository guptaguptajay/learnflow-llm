"""Vector store repository - now using pgvector instead of Qdrant."""

# Import pgvector implementation
from app.repositories.pgvector_store import VectorStoreRepository, ScoredPoint

# Re-export for backward compatibility
__all__ = ["VectorStoreRepository", "ScoredPoint"]
