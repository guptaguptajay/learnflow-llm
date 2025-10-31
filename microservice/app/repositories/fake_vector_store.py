"""No-op vector store used for tests or when pgvector is unavailable."""

from typing import Any, Dict, List, Optional


class ScoredPoint:
    def __init__(self, id: str, score: float, payload: Optional[Dict[str, Any]] = None):
        self.id = id
        self.score = score
        self.payload = payload or {}


class NoopVectorStoreRepository:
    """A minimal in-memory/no-op vector store compatible with the pgvector interface."""

    def __init__(self, dimension: int = 3072):
        self.dimension = dimension
        # store vectors in-memory keyed by collection_name
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def create_collection(self, collection_name: str, vector_size: int, distance: str = "Cosine") -> bool:
        self._store.setdefault(collection_name, {})
        return True

    def collection_exists(self, collection_name: str) -> bool:
        return collection_name in self._store

    def insert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        from uuid import uuid4

        self._store.setdefault(collection_name, {})
        vector_ids = ids or [str(uuid4()) for _ in vectors]
        for vid, vec, meta in zip(vector_ids, vectors, metadata):
            self._store[collection_name][vid] = {"embedding": vec, "payload": meta}
        return vector_ids

    def search_vectors(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[ScoredPoint]:
        # Provide deterministic empty result in tests
        return []

    def get_vectors_by_ids(self, collection_name: str, ids: List[str]) -> List[Any]:
        return [self._store.get(collection_name, {}).get(i) for i in ids if i in self._store.get(collection_name, {})]

    def delete_vectors(self, collection_name: str, ids: List[str]) -> bool:
        for vid in ids:
            self._store.get(collection_name, {}).pop(vid, None)
        return True

    def delete_collection(self, collection_name: str) -> bool:
        self._store.pop(collection_name, None)
        return True

    def get_collection_info(self, collection_name: str) -> Optional[Dict[str, Any]]:
        points = len(self._store.get(collection_name, {}))
        return {
            "name": collection_name,
            "vectors_count": points,
            "points_count": points,
            "status": "green" if points > 0 else "yellow",
        }

    def health_check(self) -> bool:
        return True


