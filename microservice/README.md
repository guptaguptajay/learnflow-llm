# GenAI Document Mapping Microservice

A senior-level GenAI microservice for document processing and knowledge mapping, built with FastAPI, LangChain, and modern vector databases.

## Features

- **Multi-format Document Processing**: Support for PDF, EPUB, and MOBI formats
- **Intelligent Chunking**: LangChain-powered semantic text splitting
- **Vector Embeddings**: State-of-the-art embeddings with OpenAI or Anthropic
- **Knowledge Mapping**: NotebookLM-style hierarchical mind map generation
- **Scalable Storage**: PostgreSQL with pgvector for embeddings and metadata
- **Clean Architecture**: Separated layers (API, Service, Repository)
- **Type Safety**: Comprehensive type hints with Pydantic V2
- **API-First Design**: Each operation is a separate API endpoint

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI API Layer                    │
│  /documents/* | /topics/* | /health                     │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                   Service Layer                         │
│  DocumentProcessor | Vectorizer | MindMapGenerator     │
│  Summarizer                                             │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│                 Repository Layer                        │
│  MetadataRepository (PostgreSQL)                        │
│  VectorStoreRepository (PostgreSQL + pgvector)          │
└─────────────────────────────────────────────────────────┘
```

## Tech Stack

- **FastAPI**: Async REST API framework
- **LangChain**: Document loaders, text splitters, LCEL chains
- **PostgreSQL + pgvector**: Database for metadata and vector embeddings
- **Pydantic V2**: Data validation and settings
- **SQLAlchemy 2.0**: ORM for database operations
- **OpenAI/Anthropic**: LLM and embedding providers

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key or Anthropic API key

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd microservice
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required environment variables:
- `OPENAI_API_KEY`: Your OpenAI API key
- `LLM_PROVIDER`: "openai" or "anthropic"
- `POSTGRES_*`: PostgreSQL connection settings (pgvector enabled)

### 3. Start with Docker Compose

```bash
docker-compose up -d
```

This will start:
- PostgreSQL with pgvector (port 5432)
- FastAPI application (port 8000)

### 4. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Workflow

### Step 1: Upload Document

```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

Response:
```json
{
  "document_id": "abc-123-xyz",
  "filename": "document.pdf",
  "format": "pdf",
  "status": "uploaded",
  "file_size_bytes": 50000,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Step 2: Process Document

```bash
curl -X POST "http://localhost:8000/documents/process" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "abc-123-xyz",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }'
```

Response:
```json
{
  "document_id": "abc-123-xyz",
  "chunks_created": 45,
  "status": "processed",
  "processing_time_seconds": 2.5
}
```

### Step 3: Vectorize Document

```bash
curl -X POST "http://localhost:8000/documents/vectorize" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "abc-123-xyz"
  }'
```

Response:
```json
{
  "document_id": "abc-123-xyz",
  "vectors_created": 45,
  "status": "vectorized",
  "processing_time_seconds": 8.3
}
```

### Step 4: Generate Topics

```bash
curl -X POST "http://localhost:8000/topics/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "abc-123-xyz",
    "num_topics": 5
  }'
```

Response:
```json
{
  "document_id": "abc-123-xyz",
  "topics": [
    {
      "id": "topic-1",
      "document_id": "abc-123-xyz",
      "title": "Introduction to Machine Learning",
      "level": 1,
      "parent_id": null,
      "summary": null,
      "vector_ids": ["vec-1", "vec-2"],
      "chunk_ids": ["chunk-1", "chunk-2"],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "processing_time_seconds": 5.2
}
```

### Step 5: Generate Subtopics

```bash
curl -X POST "http://localhost:8000/topics/subtopics/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": "topic-1",
    "num_subtopics": 3
  }'
```

### Step 6: Generate Summary

```bash
curl -X POST "http://localhost:8000/topics/summary/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": "topic-1"
  }'
```

Response:
```json
{
  "topic_id": "topic-1",
  "summary": "This section introduces the fundamental concepts of machine learning...",
  "processing_time_seconds": 3.1
}
```

### Step 7: Get Complete Text

```bash
curl -X POST "http://localhost:8000/topics/content" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": "topic-1"
  }'
```

Response:
```json
{
  "topic_id": "topic-1",
  "title": "Introduction to Machine Learning",
  "full_text": "Complete text from all associated chunks...",
  "chunk_ids": ["chunk-1", "chunk-2", "chunk-3"],
  "chunk_count": 3
}
```

## Development Setup

### Local Development (without Docker)

1. **Create virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Start PostgreSQL with pgvector**:
```bash
# PostgreSQL with pgvector
docker run -d -p 5432:5432 \
  -e POSTGRES_DB=document_mapping \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  pgvector/pgvector:pg16
```

4. **Run application**:
```bash
python -m uvicorn app.main:app --reload
```

### Running Tests

```bash
pytest tests/ -v
```

With coverage:
```bash
pytest tests/ --cov=app --cov-report=html
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking (optional)
mypy app/
```

## Project Structure

```
microservice/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── documents.py      # Document endpoints
│   │   │   ├── topics.py         # Topic endpoints
│   │   │   └── health.py         # Health check
│   │   └── dependencies.py       # Dependency injection
│   ├── core/
│   │   ├── config.py             # Settings management
│   │   └── logging.py            # Logging configuration
│   ├── services/
│   │   ├── document_processor.py # Document processing
│   │   ├── vectorizer.py         # Vectorization
│   │   ├── mindmap_generator.py  # Mind map generation
│   │   └── summarizer.py         # Summarization
│   ├── repositories/
│   │   ├── metadata_store.py     # PostgreSQL operations
│   │   ├── pgvector_store.py     # pgvector operations
│   │   └── vector_store.py       # Vector store interface
│   ├── models/
│   │   └── schemas.py            # Pydantic models
│   └── main.py                   # FastAPI application
├── tests/
│   ├── test_api.py               # API tests
│   └── test_services.py          # Service tests
├── requirements.txt              # Python dependencies
├── pyproject.toml                # Project configuration
├── docker-compose.yml            # Docker services
├── Dockerfile                    # Application container
└── README.md                     # This file
```

## Configuration

Key configuration options in `.env`:

```bash
# LLM Settings
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=50

# Mind Map Generation
MAX_TOPICS=10
MAX_SUBTOPICS_PER_TOPIC=5
MIND_MAP_DEPTH=3
```

## API Endpoints

### Documents
- `POST /documents/upload` - Upload document
- `POST /documents/process` - Process document (chunking)
- `POST /documents/vectorize` - Vectorize chunks
- `GET /documents/{document_id}` - Get document info

### Topics
- `POST /topics/generate` - Generate main topics
- `POST /topics/subtopics/generate` - Generate subtopics
- `POST /topics/summary/generate` - Generate summary
- `POST /topics/content` - Get full content
- `GET /topics/{document_id}` - Get all topics

### Health
- `GET /health` - Health check
- `GET /` - API information

## Database Schema

### Documents Table
- `id`: Unique identifier
- `filename`: Original filename
- `file_path`: Storage path
- `format`: Document format (pdf, epub, mobi)
- `status`: Processing status
- `file_size_bytes`: File size
- `metadata`: Additional metadata (JSON)
- `created_at`, `updated_at`: Timestamps

### DocumentChunks Table
- `id`: Unique identifier
- `document_id`: Foreign key to documents
- `chunk_index`: Order of chunk
- `text`: Chunk text content
- `metadata`: Chunk metadata (JSON)
- `created_at`: Timestamp

### TopicNodes Table
- `id`: Unique identifier
- `document_id`: Foreign key to documents
- `title`: Topic title
- `level`: Hierarchy level (1=topic, 2=subtopic, etc.)
- `parent_id`: Parent topic ID (nullable)
- `summary`: Generated summary (nullable)
- `created_at`, `updated_at`: Timestamps

### TopicVectorMappings Table
- `id`: Unique identifier
- `topic_id`: Foreign key to topic_nodes
- `vector_id`: Vector ID (chunk_id in embeddings table)
- `chunk_id`: Foreign key to document_chunks
- `created_at`: Timestamp

### Embeddings Table (pgvector)
- `chunk_id`: Primary key, matches document_chunks.id
- `document_id`: Foreign key reference
- `chunk_index`: Chunk position in document
- `embedding`: vector(3072) - embedding vector
- `payload`: JSONB - additional metadata

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection
psql postgresql://postgres:postgres@localhost:5432/document_mapping
```

### pgvector Issues
```bash
# Verify pgvector extension is installed
docker exec -it document_mapping_postgres psql -U postgres -d document_mapping -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# Check embeddings table
docker exec -it document_mapping_postgres psql -U postgres -d document_mapping -c "\d embeddings"
```

### API Key Issues
- Ensure your API keys are set in `.env`
- Verify the keys are valid and have sufficient credits
- Check logs for authentication errors

## Performance Considerations

- **Chunking**: Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` based on document type
- **Embeddings**: Use `text-embedding-3-large` for best quality
- **Topics**: Limit `MAX_TOPICS` to 10-15 for faster processing
- **File Size**: Large files (>50MB) may require timeout adjustments

## Security Notes

- Add authentication middleware for production
- Implement rate limiting per user/API key
- Validate file types and scan for malware
- Use environment-specific configurations
- Enable HTTPS in production
- Rotate API keys regularly

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Support

For issues and questions:
- Create an issue on GitHub
- Check API documentation at `/docs`
- Review logs in Docker containers

---

Built with ❤️ using FastAPI, LangChain, and modern AI technologies.

