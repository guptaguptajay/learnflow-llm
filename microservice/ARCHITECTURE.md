# Architecture Documentation

## System Overview

The GenAI Document Mapping Microservice is designed using clean architecture principles with clear separation of concerns across multiple layers.

## Architectural Layers

### 1. API Layer (`app/api/`)

**Purpose**: Handle HTTP requests and responses

**Components**:
- `routes/documents.py`: Document upload, processing, and vectorization endpoints
- `routes/topics.py`: Topic generation, subtopic creation, and summarization endpoints
- `routes/health.py`: Health check endpoints
- `dependencies.py`: Dependency injection for services and repositories

**Responsibilities**:
- Request validation (Pydantic models)
- Response formatting
- HTTP status code management
- Error handling and translation to HTTP errors

### 2. Service Layer (`app/services/`)

**Purpose**: Business logic and orchestration

**Components**:
- `document_processor.py`: Document loading and chunking with LangChain
- `vectorizer.py`: Embedding generation and vector operations
- `mindmap_generator.py`: LLM-powered topic extraction using LCEL
- `summarizer.py`: Content summarization using LLM

**Responsibilities**:
- Orchestrate operations across repositories
- Implement business rules
- Handle LangChain operations
- Manage LLM interactions
- Error handling and recovery

### 3. Repository Layer (`app/repositories/`)

**Purpose**: Data persistence and retrieval

**Components**:
- `metadata_store.py`: PostgreSQL operations via SQLAlchemy
- `pgvector_store.py`: PostgreSQL pgvector operations for embeddings
- `vector_store.py`: Vector store interface (exports pgvector implementation)

**Responsibilities**:
- CRUD operations
- Database-specific error handling
- Connection management
- Query optimization

### 4. Models Layer (`app/models/`)

**Purpose**: Data validation and schema definitions

**Components**:
- `schemas.py`: Pydantic V2 models for all requests/responses

**Responsibilities**:
- Data validation
- Serialization/deserialization
- Type safety
- API documentation (auto-generated)

### 5. Core Layer (`app/core/`)

**Purpose**: Cross-cutting concerns

**Components**:
- `config.py`: Application settings with Pydantic Settings
- `logging.py`: Structured logging setup

**Responsibilities**:
- Configuration management
- Logging infrastructure
- Shared utilities

## Data Flow

### Complete Workflow

```
1. Document Upload
   ┌─────────┐     ┌─────────────┐     ┌──────────────┐
   │ Client  │────>│ API Layer   │────>│ PostgreSQL   │
   └─────────┘     └─────────────┘     └──────────────┘
                           │
                           v
                   Store file locally

2. Document Processing
   ┌─────────┐     ┌─────────────┐     ┌──────────────────┐
   │ Client  │────>│ API Layer   │────>│ Document         │
   └─────────┘     └─────────────┘     │ Processor        │
                                        │ (LangChain)      │
                                        └──────────────────┘
                                                │
                                                v
                                        ┌──────────────┐
                                        │ PostgreSQL   │
                                        │ (chunks)     │
                                        └──────────────┘

3. Vectorization
   ┌─────────┐     ┌─────────────┐     ┌──────────────┐
   │ Client  │────>│ API Layer   │────>│ Vectorizer   │
   └─────────┘     └─────────────┘     │ Service      │
                                        └──────────────┘
                                                │
                                                v
                                        ┌──────────────┐
                                        │ OpenAI/      │
                                        │ Anthropic    │
                                        └──────────────┘
                                                │
                                                v
                                        ┌──────────────┐
                                        │ Qdrant       │
                                        │ (vectors)    │
                                        └──────────────┘

4. Topic Generation
   ┌─────────┐     ┌─────────────┐     ┌──────────────┐
   │ Client  │────>│ API Layer   │────>│ MindMap      │
   └─────────┘     └─────────────┘     │ Generator    │
                                        └──────────────┘
                                                │
                                                v
                                        ┌──────────────┐
                                        │ LLM          │
                                        │ (via LCEL)   │
                                        └──────────────┘
                                                │
                                                v
                                        ┌──────────────┐
                                        │ PostgreSQL   │
                                        │ (topics)     │
                                        └──────────────┘
                                                │
                                                v
                                        ┌──────────────┐
                                        │ Qdrant       │
                                        │ (semantic    │
                                        │  search)     │
                                        └──────────────┘
```

## Database Schema

### PostgreSQL Tables

#### documents
- Stores document metadata
- Links to chunks and topics
- Tracks processing status

#### document_chunks
- Stores text chunks
- Links to document
- Indexed for retrieval

#### topic_nodes
- Hierarchical mind map structure
- Self-referential (parent_id)
- Stores summaries

#### topic_vector_mappings
- Links topics to vectors
- Links topics to chunks
- Many-to-many relationship

### pgvector Embeddings Table

All embeddings stored in single `embeddings` table:
- Primary key: `chunk_id` (matches document_chunks.id)
- Indexed by: `document_id` for fast filtering
- Vector column: `embedding vector(3072)` with IVFFlat cosine index
- Payload: JSONB for flexible metadata storage
- Each document's embeddings filtered by `document_id`

## LangChain Integration

### Document Loading
```python
PyPDFLoader          # For PDF files
UnstructuredEPubLoader  # For EPUB files
UnstructuredFileLoader  # For MOBI files
```

### Text Splitting
```python
RecursiveCharacterTextSplitter
- chunk_size: configurable (default 1000)
- chunk_overlap: configurable (default 200)
- separators: ["\n\n", "\n", ". ", " ", ""]
```

### Embeddings
```python
OpenAIEmbeddings
- model: text-embedding-3-large
- dimensions: 3072
```

### LLM Chains (LCEL)
```python
# Topic Extraction
prompt = ChatPromptTemplate.from_messages([...])
structured_llm = llm.with_structured_output(TopicsListOutput)
chain = prompt | structured_llm

# Summarization
prompt = ChatPromptTemplate.from_messages([...])
chain = prompt | llm
```

## Design Patterns

### 1. Dependency Injection
- Services injected via FastAPI dependencies
- Enables testing with mocks
- Centralizes instance management

### 2. Repository Pattern
- Abstract data access
- Easy to swap implementations
- Consistent interface

### 3. Service Layer Pattern
- Business logic separated from API
- Reusable across different interfaces
- Testable independently

### 4. Structured Output with Pydantic
- Type-safe LLM responses
- Validation at LLM output level
- Better error handling

## Scalability Considerations

### Horizontal Scaling
- Stateless API design
- Session-free architecture
- Load balancer ready

### Database Scaling
- PostgreSQL: Read replicas for queries
- pgvector: Partitioning by document_id for large datasets
- Connection pooling enabled
- IVFFlat index tuning for vector search performance

### Performance Optimization
- Batch operations for vectors
- Chunk-level caching potential
- Async operations throughout

### Resource Management
- Configurable chunk sizes
- Rate limiting ready
- Token counting for cost control

## Security Considerations

### Current Implementation
- CORS middleware (configured for development)
- Input validation via Pydantic
- File size limits
- SQL injection protection (SQLAlchemy ORM)

### Production Recommendations
- Add authentication middleware (JWT, API keys)
- Implement rate limiting per user
- Enable HTTPS only
- Add file type validation and scanning
- Encrypt sensitive data at rest
- Use secrets management (Vault, AWS Secrets Manager)
- Enable audit logging

## Error Handling

### API Layer
- HTTP status codes (400, 404, 500)
- Structured error responses
- Detailed error messages in development

### Service Layer
- Business exception types
- Retry logic for transient failures
- Graceful degradation

### Repository Layer
- Database-specific error handling
- Connection retry logic
- Transaction management

## Monitoring and Observability

### Logging
- Structured logging with correlation IDs
- Different log levels per environment
- Centralized logging ready

### Health Checks
- Database connectivity
- Vector store connectivity
- API endpoint health

### Future Enhancements
- LangSmith/LangFuse integration for LLM tracing
- Prometheus metrics
- Distributed tracing (OpenTelemetry)
- Performance monitoring (APM)

## Testing Strategy

### Unit Tests
- Service layer logic
- Repository operations
- Model validation

### Integration Tests
- API endpoints
- Database operations
- External service mocking

### End-to-End Tests
- Complete workflows
- Error scenarios
- Performance testing

## Deployment

### Docker Compose (Development)
- All services in containers
- Volume mounts for persistence
- Easy local development

### Production Deployment Options
1. **Kubernetes**
   - Helm charts for deployment
   - Horizontal pod autoscaling
   - Service mesh integration

2. **Cloud Services**
   - AWS: ECS/EKS + RDS (with pgvector)
   - GCP: GKE + Cloud SQL (with pgvector)
   - Azure: AKS + Azure Database for PostgreSQL (with pgvector)

3. **Serverless Options**
   - API: AWS Lambda + API Gateway
   - Processing: Background workers
   - Databases: Managed services

## Future Enhancements

### Planned Features
1. Incremental document updates
2. Document versioning
3. Multi-user support with authentication
4. Redis caching layer
5. Background task processing (Celery)
6. Streaming responses for large operations
7. GraphQL API option
8. WebSocket support for real-time updates
9. Advanced search with filters
10. Export capabilities (JSON, Markdown, etc.)

### Technical Improvements
1. API versioning
2. Rate limiting implementation
3. Circuit breakers for external services
4. Advanced monitoring dashboards
5. Automated backup strategies
6. Multi-region deployment support
7. A/B testing framework
8. Feature flags

