# Project Structure Overview

## Complete File Tree

```
microservice/
│
├── 📱 Application Code (app/)
│   ├── __init__.py
│   ├── main.py                          # FastAPI application entry point
│   │
│   ├── 🌐 API Layer (api/)
│   │   ├── __init__.py
│   │   ├── dependencies.py              # Dependency injection
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── documents.py             # Document endpoints
│   │       ├── topics.py                # Topic endpoints
│   │       └── health.py                # Health checks
│   │
│   ├── ⚙️ Core (core/)
│   │   ├── __init__.py
│   │   ├── config.py                    # Pydantic settings
│   │   └── logging.py                   # Structured logging
│   │
│   ├── 💼 Business Logic (services/)
│   │   ├── __init__.py
│   │   ├── document_processor.py        # LangChain document processing
│   │   ├── vectorizer.py                # Embedding generation
│   │   ├── mindmap_generator.py         # LLM topic generation (LCEL)
│   │   └── summarizer.py                # LLM summarization
│   │
│   ├── 🗄️ Data Access (repositories/)
│   │   ├── __init__.py
│   │   ├── metadata_store.py            # PostgreSQL (SQLAlchemy)
│   │   ├── pgvector_store.py            # pgvector operations
│   │   └── vector_store.py              # Vector store interface
│   │
│   └── 📋 Models (models/)
│       ├── __init__.py
│       └── schemas.py                    # Pydantic V2 models
│
├── 🧪 Tests (tests/)
│   ├── __init__.py
│   ├── test_api.py                      # API endpoint tests
│   └── test_services.py                 # Service layer tests
│
├── 📜 Scripts (scripts/)
│   ├── __init__.py
│   ├── init_db.py                       # Database initialization
│   ├── example_usage.py                 # Complete workflow example
│   ├── start.sh                         # Quick start script
│   └── stop.sh                          # Stop services script
│
├── 🐳 Docker Configuration
│   ├── Dockerfile                       # Multi-stage build
│   ├── docker-compose.yml               # Services orchestration
│   └── .dockerignore                    # Docker ignore rules
│
├── ⚙️ Configuration Files
│   ├── requirements.txt                 # Python dependencies
│   ├── pyproject.toml                   # Project configuration
│   ├── .env.example                     # Environment template
│   ├── .gitignore                       # Git ignore rules
│   └── .cursorignore                    # Cursor ignore rules
│
├── 📚 Documentation
│   ├── README.md                        # Main documentation
│   ├── ARCHITECTURE.md                  # System architecture
│   ├── CONTRIBUTING.md                  # Development guide
│   ├── IMPLEMENTATION_SUMMARY.md        # Implementation overview
│   ├── QUICK_REFERENCE.md               # Quick reference guide
│   └── PROJECT_STRUCTURE.md             # This file
│
└── 🔧 Tools & Utilities
    └── postman_collection.json          # API testing collection
```

## Layer Breakdown

### 1️⃣ API Layer (`app/api/`)
**Purpose**: HTTP interface for the service

- **routes/documents.py** (260 lines)
  - `POST /documents/upload` - Upload document
  - `POST /documents/process` - Process document
  - `POST /documents/vectorize` - Vectorize chunks
  - `GET /documents/{id}` - Get document info

- **routes/topics.py** (220 lines)
  - `POST /topics/generate` - Generate topics
  - `POST /topics/subtopics/generate` - Generate subtopics
  - `POST /topics/summary/generate` - Generate summary
  - `POST /topics/content` - Get full content
  - `GET /topics/{document_id}` - List topics

- **routes/health.py** (40 lines)
  - `GET /health` - Health check
  - `GET /` - API info

- **dependencies.py** (80 lines)
  - Dependency injection setup
  - Service factory functions

### 2️⃣ Service Layer (`app/services/`)
**Purpose**: Business logic and LangChain operations

- **document_processor.py** (150 lines)
  - Document loading (PDF, EPUB, MOBI)
  - Text chunking with RecursiveCharacterTextSplitter
  - Metadata extraction

- **vectorizer.py** (180 lines)
  - Embedding generation (OpenAI/Anthropic)
  - Batch vectorization
  - Semantic search

- **mindmap_generator.py** (230 lines)
  - LLM-powered topic extraction
  - LCEL chain composition
  - Structured output with Pydantic
  - Topic-vector mapping

- **summarizer.py** (120 lines)
  - Content summarization
  - Topic content retrieval
  - LLM chain for summaries

### 3️⃣ Repository Layer (`app/repositories/`)
**Purpose**: Data persistence and retrieval

- **metadata_store.py** (380 lines)
  - SQLAlchemy models (Document, Chunk, Topic, Mapping)
  - CRUD operations
  - Relationship management
  - PostgreSQL specific operations

- **pgvector_store.py** (~450 lines)
  - PostgreSQL pgvector operations
  - Extension and table management
  - Vector CRUD with SQLAlchemy
  - Cosine similarity search with IVFFlat index
  - Retry logic

- **vector_store.py** (~10 lines)
  - Interface module
  - Re-exports pgvector implementation

### 4️⃣ Models Layer (`app/models/`)
**Purpose**: Data validation and schema

- **schemas.py** (250 lines)
  - Request models (Pydantic V2)
  - Response models
  - Enums (DocumentStatus, DocumentFormat)
  - Validation rules

### 5️⃣ Core Layer (`app/core/`)
**Purpose**: Cross-cutting concerns

- **config.py** (110 lines)
  - Pydantic Settings
  - Environment variable management
  - Configuration validation

- **logging.py** (60 lines)
  - Structured logging
  - Correlation ID support
  - Log level management

## File Size Overview

### Large Files (>200 lines)
- `pgvector_store.py` - 450 lines (pgvector operations)
- `metadata_store.py` - 380 lines (SQLAlchemy models + repository)
- `documents.py` - 260 lines (Document API endpoints)
- `schemas.py` - 250 lines (Pydantic models)
- `mindmap_generator.py` - 230 lines (Topic generation)
- `topics.py` - 220 lines (Topic API endpoints)

### Medium Files (100-200 lines)
- `vectorizer.py` - 180 lines
- `document_processor.py` - 150 lines
- `summarizer.py` - 120 lines
- `config.py` - 110 lines

### Small Files (<100 lines)
- `dependencies.py` - 80 lines
- `logging.py` - 60 lines
- `health.py` - 40 lines
- Various `__init__.py` files

## Technology Stack by Layer

### API Layer
- FastAPI
- Pydantic V2
- Python async/await

### Service Layer
- LangChain
  - Document Loaders
  - Text Splitters
  - LCEL
  - Prompt Templates
- OpenAI/Anthropic SDKs

### Repository Layer
- SQLAlchemy 2.0
- Psycopg 3
- pgvector (Python bindings)

### Testing
- Pytest
- Pytest-asyncio
- HTTPX (TestClient)

## Key Design Patterns

### 1. Repository Pattern
```
Service Layer → Repository Interface → Database
```
Benefits: Abstraction, testability, swappable implementations

### 2. Dependency Injection
```
FastAPI Dependencies → Service Factory → Service Instance
```
Benefits: Loose coupling, easy testing, lifecycle management

### 3. Clean Architecture
```
API → Service → Repository → Database
```
Benefits: Separation of concerns, maintainability, scalability

### 4. Chain of Responsibility (LCEL)
```
Prompt → LLM → Structured Output → Validation
```
Benefits: Composability, type safety, error handling

## Data Flow Diagram

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       v
┌─────────────┐
│  API Layer  │
│ (FastAPI)   │
└──────┬──────┘
       │
       v
┌─────────────┐
│   Service   │
│   Layer     │
└──────┬──────┘
       │
       v
┌─────────────┐
│ Repository  │
│   Layer     │
└──────┬──────┘
       │
       v
┌─────────────┐
│  Database   │
│ (PostgreSQL │
│ + pgvector) │
└─────────────┘
```

## Request Flow Example

### Document Upload Flow
```
1. Client → POST /documents/upload
2. API → documents.upload_document()
3. API → Save file to disk
4. API → metadata_repo.create_document()
5. PostgreSQL → Store document record
6. API → Return DocumentUploadResponse
7. Client ← JSON response
```

### Topic Generation Flow
```
1. Client → POST /topics/generate
2. API → topics.generate_topics()
3. Service → mindmap_service.generate_topics()
4. Service → Get chunks from PostgreSQL
5. Service → Create LCEL chain
6. Service → Call LLM with structured output
7. Service → Store topics in PostgreSQL
8. Service → Semantic search in pgvector
9. Service → Create topic-vector mappings
10. API → Return GenerateTopicsResponse
11. Client ← JSON response with topics
```

## Dependencies Graph

```
main.py
  ↓
routes/ ←─ dependencies.py
  ↓              ↓
services/    repositories/
  ↓              ↓
models/      core/config.py
  ↓
core/logging.py
```

## Code Statistics

- **Total Files**: 42
- **Python Files**: 26
- **Configuration Files**: 8
- **Documentation Files**: 6
- **Script Files**: 4

- **Total Lines of Code**: ~3,500
- **Application Code**: ~2,200
- **Test Code**: ~400
- **Configuration**: ~300
- **Documentation**: ~2,500 (separate)

## Module Import Map

```python
# API Layer imports
from app.api.dependencies import get_*_service
from app.models.schemas import *Request, *Response

# Service Layer imports
from app.repositories.metadata_store import MetadataRepository
from app.repositories.vector_store import VectorStoreRepository
from app.core.config import get_settings
from langchain import *

# Repository Layer imports
from sqlalchemy import *
from pgvector.sqlalchemy import Vector
from app.core.config import get_settings

# Models Layer imports
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
```

## Testing Coverage Map

```
tests/
├── test_api.py
│   ├── TestHealthEndpoints (2 tests)
│   ├── TestDocumentEndpoints (4 tests)
│   └── TestTopicEndpoints (5 tests)
│
└── test_services.py
    └── TestMetadataRepository (7 tests)
```

## Documentation Map

```
docs/
├── README.md                     # User guide, setup, API docs
├── ARCHITECTURE.md               # System design, patterns
├── CONTRIBUTING.md               # Development guidelines
├── IMPLEMENTATION_SUMMARY.md     # What was built
├── QUICK_REFERENCE.md            # Command cheatsheet
└── PROJECT_STRUCTURE.md          # This file
```

## Environment Variables Map

```
.env
├── Application
│   ├── APP_NAME
│   ├── DEBUG
│   └── LOG_LEVEL
├── Databases
│   ├── POSTGRES_*
│   └── QDRANT_*
├── LLM
│   ├── OPENAI_API_KEY
│   ├── ANTHROPIC_API_KEY
│   └── LLM_PROVIDER
├── Processing
│   ├── CHUNK_SIZE
│   └── CHUNK_OVERLAP
└── Mind Mapping
    ├── MAX_TOPICS
    └── MAX_SUBTOPICS_PER_TOPIC
```

## Quick Navigation

- **Need to add API endpoint?** → `app/api/routes/`
- **Need to add business logic?** → `app/services/`
- **Need to add database operation?** → `app/repositories/`
- **Need to add data model?** → `app/models/schemas.py`
- **Need to change config?** → `app/core/config.py` or `.env`
- **Need to write tests?** → `tests/`
- **Need to add utility script?** → `scripts/`

---

*This structure follows clean architecture principles and is designed for scalability and maintainability.*

