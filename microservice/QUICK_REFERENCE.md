# Quick Reference Guide

## Essential Commands

### Setup & Start
```bash
# First time setup
cp .env.example .env
# Edit .env with your API keys

# Start all services
./scripts/start.sh

# Stop all services
./scripts/stop.sh

# Initialize database only
python scripts/init_db.py
```

### Development
```bash
# Start in development mode
python -m uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Format code
black app/ tests/

# Lint code
ruff check app/ tests/
```

## API Workflow

### Complete Document Processing Flow

```bash
# 1. Upload
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@document.pdf"
# Returns: {"document_id": "abc-123"}

# 2. Process
curl -X POST http://localhost:8000/documents/process \
  -H "Content-Type: application/json" \
  -d '{"document_id": "abc-123"}'

# 3. Vectorize
curl -X POST http://localhost:8000/documents/vectorize \
  -H "Content-Type: application/json" \
  -d '{"document_id": "abc-123"}'

# 4. Generate Topics
curl -X POST http://localhost:8000/topics/generate \
  -H "Content-Type: application/json" \
  -d '{"document_id": "abc-123", "num_topics": 5}'
# Returns: {"topics": [{"id": "topic-1", ...}]}

# 5. Generate Subtopics
curl -X POST http://localhost:8000/topics/subtopics/generate \
  -H "Content-Type: application/json" \
  -d '{"topic_id": "topic-1", "num_subtopics": 3}'

# 6. Generate Summary
curl -X POST http://localhost:8000/topics/summary/generate \
  -H "Content-Type: application/json" \
  -d '{"topic_id": "topic-1"}'

# 7. Get Content
curl -X POST http://localhost:8000/topics/content \
  -H "Content-Type: application/json" \
  -d '{"topic_id": "topic-1"}'
```

## Key Files

### Configuration
- `.env` - Environment variables (API keys, settings)
- `app/core/config.py` - Settings management
- `docker-compose.yml` - Service orchestration

### API Routes
- `app/api/routes/documents.py` - Document endpoints
- `app/api/routes/topics.py` - Topic endpoints
- `app/api/routes/health.py` - Health checks

### Business Logic
- `app/services/document_processor.py` - Document processing
- `app/services/vectorizer.py` - Embeddings
- `app/services/mindmap_generator.py` - Topic generation
- `app/services/summarizer.py` - Summarization

### Data Access
- `app/repositories/metadata_store.py` - PostgreSQL metadata
- `app/repositories/pgvector_store.py` - PostgreSQL pgvector embeddings
- `app/repositories/vector_store.py` - Vector store interface

## Important URLs

### Local Development
- API Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Database Connections
- PostgreSQL (with pgvector): `postgresql://postgres:postgres@localhost:5432/document_mapping`

## Environment Variables

### Required
```env
OPENAI_API_KEY=sk-...        # OpenAI API key
```

### Optional
```env
LLM_PROVIDER=openai          # openai or anthropic
CHUNK_SIZE=1000              # Text chunk size
CHUNK_OVERLAP=200            # Chunk overlap
MAX_TOPICS=10                # Max topics per document
MAX_FILE_SIZE_MB=50          # Max upload size
```

## Common Issues

### "Database connection failed"
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### "pgvector extension not found"
```bash
# Check pgvector extension
docker exec -it document_mapping_postgres psql -U postgres -d document_mapping -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# If not found, verify using pgvector image
docker-compose down
docker-compose up -d
```

### "API key invalid"
```bash
# Check .env file exists
cat .env | grep API_KEY

# Ensure no quotes around API keys
# Wrong: OPENAI_API_KEY="sk-..."
# Right: OPENAI_API_KEY=sk-...
```

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test
```bash
pytest tests/test_api.py::TestDocumentEndpoints::test_upload_document -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

## Docker Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f postgres
```

### Restart Service
```bash
docker-compose restart api
```

### Rebuild
```bash
docker-compose up -d --build
```

### Clean Up
```bash
# Stop and remove containers
docker-compose down

# Remove volumes too (deletes data!)
docker-compose down -v
```

## Database Operations

### Connect to PostgreSQL
```bash
docker exec -it document_mapping_postgres psql -U postgres -d document_mapping
```

### Useful SQL Queries
```sql
-- List all documents
SELECT id, filename, status, created_at FROM documents;

-- Count chunks per document
SELECT document_id, COUNT(*) FROM document_chunks GROUP BY document_id;

-- List all topics
SELECT id, title, level, parent_id FROM topic_nodes;

-- Get topics for a document
SELECT * FROM topic_nodes WHERE document_id = 'abc-123';
```

## Monitoring

### Check Service Health
```bash
curl http://localhost:8000/health
```

### Check Embeddings Count
```bash
docker exec -it document_mapping_postgres psql -U postgres -d document_mapping -c "SELECT document_id, COUNT(*) FROM embeddings GROUP BY document_id;"
```

### View API Metrics
```bash
# Request logs
docker-compose logs api | grep "POST\|GET"

# Error logs
docker-compose logs api | grep "ERROR"
```

## Development Tips

### Hot Reload
```bash
# FastAPI auto-reloads on code changes
python -m uvicorn app.main:app --reload
```

### Debug Mode
```bash
# Set in .env
DEBUG=True
LOG_LEVEL=DEBUG
```

### Test with Example Script
```bash
python scripts/example_usage.py
```

### Import Postman Collection
1. Open Postman
2. Import `postman_collection.json`
3. Set variables: `document_id`, `topic_id`
4. Use collection for testing

## Performance Tuning

### Adjust Chunk Size
```env
CHUNK_SIZE=1500          # Larger chunks, fewer API calls
CHUNK_OVERLAP=300        # More overlap, better context
```

### Adjust Topic Limits
```env
MAX_TOPICS=5             # Fewer topics, faster processing
MAX_SUBTOPICS_PER_TOPIC=3
```

### Database Optimization
```sql
-- Add indexes if needed
CREATE INDEX idx_chunks_document ON document_chunks(document_id);
CREATE INDEX idx_topics_document ON topic_nodes(document_id);
```

## Troubleshooting Checklist

- [ ] Docker is running
- [ ] .env file exists with API keys
- [ ] PostgreSQL with pgvector is healthy (check logs)
- [ ] pgvector extension is enabled
- [ ] API is responding (check /health)
- [ ] No firewall blocking ports 5432, 8000
- [ ] Sufficient disk space for uploads
- [ ] API key has sufficient credits

## File Locations

### Uploads
- Default: `./uploads/`
- Configure: `UPLOAD_DIR` in .env

### Temp Files
- Default: `./temp/`
- Configure: `TEMP_DIR` in .env

### Logs
- API: Docker logs
- PostgreSQL: Docker logs

## Security Checklist (Production)

- [ ] Change default passwords
- [ ] Enable HTTPS
- [ ] Add authentication
- [ ] Implement rate limiting
- [ ] Set up firewall rules
- [ ] Use secrets management
- [ ] Enable audit logging
- [ ] Scan uploaded files
- [ ] Restrict CORS origins
- [ ] Use strong API keys

## Next Steps

1. Review ARCHITECTURE.md for system design
2. Read CONTRIBUTING.md for development workflow
3. Check README.md for detailed documentation
4. Test with example_usage.py
5. Import Postman collection for API testing

## Support

- GitHub Issues: For bugs and features
- Documentation: README.md, ARCHITECTURE.md
- API Docs: http://localhost:8000/docs
- Example: scripts/example_usage.py

---

Last Updated: 2024
Version: 0.1.0

