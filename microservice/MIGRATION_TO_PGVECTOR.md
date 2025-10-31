# Migration from Qdrant to pgvector

This document summarizes the migration from Qdrant to PostgreSQL with pgvector extension.

## What Changed

### Infrastructure
- **Removed**: Qdrant service from `docker-compose.yml`
- **Updated**: PostgreSQL image from `postgres:16-alpine` to `pgvector/pgvector:pg16`
- **Removed**: Qdrant volume definition
- **Removed**: Qdrant environment variables and dependencies

### Dependencies
- **Removed**: `qdrant-client>=1.7.0`
- **Added**: `pgvector>=0.2.5`

### Configuration (`app/core/config.py`)
- **Removed**: 
  - `qdrant_host`
  - `qdrant_port`
  - `qdrant_collection_name`
  - `qdrant_api_key`
  - `qdrant_url` property
- **Added**:
  - `pgvector_dimension` (default: 3072)
  - `pgvector_ivfflat_lists` (default: 100)

### Code Changes

#### New Files
- `app/repositories/pgvector_store.py` (~450 lines)
  - Complete pgvector implementation
  - SQLAlchemy-based vector operations
  - IVFFlat index management
  - Cosine similarity search
  - Compatible interface with old Qdrant repository

#### Modified Files
- `app/repositories/vector_store.py`
  - Now a thin interface module
  - Re-exports `VectorStoreRepository` and `ScoredPoint` from `pgvector_store`

- `app/services/vectorizer.py`
  - Updated collection naming from `{qdrant_collection_name}_{document_id}` to `documents_{document_id}`
  - Updated comments to reference pgvector instead of Qdrant

- `app/api/routes/documents.py`
  - Updated docstring from "Qdrant" to "pgvector"

### Database Schema

#### New Table: `embeddings`
```sql
CREATE TABLE embeddings (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(3072) NOT NULL,
    payload JSONB
);

CREATE INDEX idx_embeddings_doc ON embeddings(document_id);
CREATE INDEX idx_embeddings_doc_chunk ON embeddings(document_id, chunk_index);
CREATE INDEX idx_embeddings_embedding_cosine ON embeddings 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### Documentation Updates
All documentation files updated to reflect pgvector:
- `README.md`
- `ARCHITECTURE.md`
- `QUICK_REFERENCE.md`
- `CONTRIBUTING.md`
- `PROJECT_STRUCTURE.md`

## Key Differences

### Storage Model
**Before (Qdrant):**
- Each document had its own collection: `documents_{document_id}`
- Collections isolated by document

**After (pgvector):**
- Single `embeddings` table for all documents
- Filter by `document_id` for per-document queries

### Search
**Before (Qdrant):**
```python
results = client.search(
    collection_name=f"documents_{document_id}",
    query_vector=embedding,
    limit=10
)
```

**After (pgvector):**
```sql
SELECT chunk_id, payload, (1 - (embedding <=> :query_vector) / 2) as score
FROM embeddings
WHERE document_id = :document_id
ORDER BY embedding <=> :query_vector
LIMIT 10;
```

### Distance Metric
- Qdrant used native cosine distance
- pgvector uses `<=>` operator for cosine distance
- Scores normalized: `1 - (distance / 2)` for similarity

## Migration Steps for Existing Data

If you have existing data in Qdrant, you'll need to:

1. **Export from Qdrant**:
   ```python
   # For each document's collection
   points = qdrant_client.scroll(collection_name=collection_name)
   # Extract vectors and metadata
   ```

2. **Import to pgvector**:
   ```python
   from app.repositories.pgvector_store import VectorStoreRepository
   
   vector_repo = VectorStoreRepository()
   vector_repo.insert_vectors(
       collection_name=f"documents_{document_id}",
       vectors=vectors,
       metadata=metadata,
       ids=chunk_ids
   )
   ```

3. **Or Re-vectorize**:
   Simply re-run the vectorization endpoint for each document.

## Performance Considerations

### Indexing
- pgvector uses IVFFlat index for approximate nearest neighbor search
- Index created automatically on first collection creation
- Run `ANALYZE embeddings;` after bulk inserts for optimal performance

### Tuning
- Adjust `pgvector_ivfflat_lists` based on dataset size
- General rule: `lists = rows / 1000` (with min 10, max 1000)
- For 100K embeddings: lists = 100
- For 1M embeddings: lists = 1000

### Query Performance
- Filters on `document_id` use B-tree index (fast)
- Vector search uses IVFFlat index (approximate but fast)
- Combined queries benefit from both indexes

## Rollback Plan

If you need to rollback to Qdrant:

1. Revert code changes:
   ```bash
   git checkout HEAD~1 -- app/repositories/
   git checkout HEAD~1 -- docker-compose.yml
   git checkout HEAD~1 -- requirements.txt
   git checkout HEAD~1 -- app/core/config.py
   ```

2. Restore Qdrant service:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

3. Re-vectorize documents or restore Qdrant backup

## Benefits of pgvector

1. **Simplified Infrastructure**: One database instead of two
2. **Transactional Consistency**: Embeddings and metadata in same DB
3. **Easier Backups**: Single database to backup
4. **Cost Savings**: No separate vector DB service to run/manage
5. **Familiar Tooling**: Use standard PostgreSQL tools and clients

## Limitations to Consider

1. **Scale**: Qdrant may perform better at very large scale (10M+ vectors)
2. **Features**: Qdrant has more advanced filtering and payload indexing
3. **Index Types**: pgvector currently supports IVFFlat and HNSW; Qdrant has more options

## Testing

All existing tests continue to work:
- Unit tests don't depend on specific vector DB
- Integration tests use the same repository interface
- API tests are unchanged

Run tests:
```bash
pytest tests/ -v
```

## Next Steps

1. Start services: `docker-compose up -d`
2. Initialize database: `python scripts/init_db.py`
3. Upload and process documents as before
4. Verify health check: `curl http://localhost:8000/health`

## Support

If you encounter issues:
1. Check pgvector extension: `SELECT * FROM pg_extension WHERE extname = 'vector';`
2. Verify table exists: `\d embeddings`
3. Check logs: `docker-compose logs postgres`
4. Review health endpoint: `/health` should show vector_store as healthy

