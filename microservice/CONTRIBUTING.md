# Contributing Guide

Thank you for considering contributing to the GenAI Document Mapping Microservice!

## Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Git
- OpenAI or Anthropic API key

### Development Setup

1. **Fork and Clone**
```bash
git clone https://github.com/your-username/genai-document-mapping.git
cd genai-document-mapping/microservice
```

2. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies**
```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov black ruff mypy
```

4. **Setup Environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Start Services**
```bash
docker-compose up -d postgres
```

6. **Initialize Database**
```bash
python scripts/init_db.py
```

7. **Run Application**
```bash
python -m uvicorn app.main:app --reload
```

## Development Workflow

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes
- Follow the code style guidelines
- Write tests for new features
- Update documentation

### 3. Run Tests
```bash
pytest tests/ -v
```

### 4. Format and Lint
```bash
# Format code
black app/ tests/

# Check linting
ruff check app/ tests/

# Fix auto-fixable issues
ruff check --fix app/ tests/
```

### 5. Commit Changes
```bash
git add .
git commit -m "feat: add your feature description"
```

Use conventional commit messages:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` code style changes
- `refactor:` code refactoring
- `test:` test additions or changes
- `chore:` maintenance tasks

### 6. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Create a Pull Request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (if UI changes)
- Test results

## Code Style Guidelines

### Python Style
- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use type hints for all functions
- Write docstrings for all public functions

### Example Function
```python
def process_document(
    document_id: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[DocumentChunk]:
    """Process a document by loading and chunking it.

    Args:
        document_id: Unique document identifier
        chunk_size: Size of each text chunk
        chunk_overlap: Overlap between consecutive chunks

    Returns:
        List of created DocumentChunk instances

    Raises:
        ValueError: If document not found or invalid parameters
        ProcessingError: If document processing fails
    """
    # Implementation
    pass
```

### Project Structure
- API logic in `app/api/routes/`
- Business logic in `app/services/`
- Data access in `app/repositories/`
- Models in `app/models/`
- Tests in `tests/`

## Testing Guidelines

### Unit Tests
Test individual functions and classes:
```python
def test_create_document(repo):
    """Test creating a document."""
    doc = repo.create_document(
        filename="test.pdf",
        file_path="/tmp/test.pdf",
        format="pdf",
        file_size_bytes=1000,
    )
    assert doc.id is not None
    assert doc.status == "uploaded"
```

### Integration Tests
Test API endpoints:
```python
def test_upload_document():
    """Test document upload endpoint."""
    with open("test.pdf", "rb") as f:
        response = client.post(
            "/documents/upload",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
    assert response.status_code == 201
```

### Test Coverage
- Aim for >80% code coverage
- Focus on critical paths
- Test error handling

### Run Tests with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

## Documentation

### Code Documentation
- Docstrings for all public functions
- Type hints for all parameters
- Examples in docstrings when helpful

### API Documentation
- FastAPI auto-generates from code
- Keep Pydantic models well-documented
- Add descriptions to all fields

### README Updates
- Update README.md for new features
- Add examples for new endpoints
- Update architecture docs if needed

## Pull Request Process

1. **Ensure Tests Pass**
   - All tests must pass
   - No linting errors
   - Code coverage maintained or improved

2. **Update Documentation**
   - README.md if needed
   - API documentation
   - Code comments

3. **PR Description**
   - What: What changes were made
   - Why: Why the changes were necessary
   - How: How the changes work
   - Testing: How it was tested

4. **Review Process**
   - Address review comments
   - Keep PR scope focused
   - Rebase if needed

5. **Merging**
   - Squash commits if many small commits
   - Use descriptive merge message
   - Delete branch after merge

## Architecture Guidelines

### Adding New Endpoints

1. **Define Pydantic Models** (`app/models/schemas.py`)
```python
class NewFeatureRequest(BaseModel):
    """Request model for new feature."""
    param1: str
    param2: int = Field(default=10, ge=1)
```

2. **Create Service** (`app/services/new_feature.py`)
```python
class NewFeatureService:
    """Service for new feature."""
    
    def __init__(self, repo: Repository):
        self.repo = repo
    
    def process(self, request: NewFeatureRequest) -> Result:
        """Process new feature request."""
        # Implementation
        pass
```

3. **Add Repository Methods** (if needed)
```python
def new_data_operation(self, params) -> Result:
    """Perform new data operation."""
    # Implementation
    pass
```

4. **Create Route** (`app/api/routes/new_feature.py`)
```python
@router.post("/new-feature", response_model=NewFeatureResponse)
async def new_feature(
    request: NewFeatureRequest,
    service: NewFeatureService = Depends(get_new_feature_service),
) -> NewFeatureResponse:
    """New feature endpoint."""
    try:
        result = service.process(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

5. **Add Tests**
```python
def test_new_feature():
    """Test new feature."""
    response = client.post("/new-feature", json={"param1": "value"})
    assert response.status_code == 200
```

### Database Changes

1. Update SQLAlchemy models in `metadata_store.py`
2. Create migration script if needed
3. Update repository methods
4. Test with SQLite in-memory first
5. Test with PostgreSQL

### LangChain Integration

1. Use LCEL for chains
2. Implement structured output with Pydantic
3. Add proper error handling
4. Consider rate limiting
5. Add logging for debugging

## Common Tasks

### Adding a New Document Format

1. Add format to `DocumentFormat` enum
2. Update `DocumentProcessorService.load_document()`
3. Add appropriate LangChain loader
4. Update tests
5. Update README

### Adding a New LLM Provider

1. Update `Settings` in `config.py`
2. Add provider initialization in services
3. Update environment variables
4. Test with new provider
5. Update documentation

### Optimizing Performance

1. Identify bottleneck (profiling)
2. Add caching if appropriate
3. Optimize database queries
4. Batch operations when possible
5. Measure improvement

## Questions or Issues?

- Create an issue on GitHub
- Include logs and error messages
- Provide steps to reproduce
- Tag appropriately (bug, feature, question)

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Keep discussions professional

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

