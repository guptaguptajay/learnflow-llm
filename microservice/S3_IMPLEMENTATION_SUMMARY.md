# S3 Storage Integration - Implementation Summary

## Objective

Replace local file storage with AWS S3 for document uploads, with a centralized and reusable storage service layer that other services can leverage.

## Implementation Completed

### ✅ 1. Configuration Layer (`app/core/config.py`)

Added AWS/S3 settings to the Settings class:

```python
# AWS/S3 Settings
aws_region: str = Field(default="us-east-1")
aws_access_key_id: str | None = Field(default=None)
aws_secret_access_key: str | None = Field(default=None)
aws_session_token: str | None = Field(default=None)
s3_bucket_name: str | None = Field(default=None)
s3_endpoint_url: str | None = Field(default=None)
s3_prefix: str = Field(default="documents/")
use_s3_storage: bool = Field(default=True)
```

All settings are environment-driven and support optional credentials.

### ✅ 2. Storage Service Layer

Created a reusable abstraction at `app/services/storage/`:

**`base.py`** - Abstract interface:
- `upload_bytes()` - Upload data
- `download_to_path()` - Download to local file
- `get_uri()` - Get storage URI
- `delete()` - Delete object

**`s3_storage.py`** - S3 implementation:
- Full boto3 integration
- Automatic directory creation for downloads
- Proper error handling with ClientError
- Support for custom endpoints (LocalStack/MinIO)
- Helper method `extract_key_from_uri()` for S3 URI parsing

### ✅ 3. Dependency Injection (`app/api/dependencies.py`)

Added storage service provider:

```python
@lru_cache()
def get_storage_service() -> StorageService:
    settings = get_settings()
    
    if settings.use_s3_storage and settings.s3_bucket_name:
        return S3StorageService(
            bucket=settings.s3_bucket_name,
            region=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
            session_token=settings.aws_session_token,
        )
    else:
        raise ValueError("S3 storage is required. Set USE_S3_STORAGE=true and S3_BUCKET in .env")
```

Updated `get_document_processor_service()` to inject storage service.

### ✅ 4. Upload API (`app/api/routes/documents.py`)

**Before:**
- Saved file locally to `./uploads/`
- Stored local path in database

**After:**
- Generates S3 key: `documents/{uuid}_{filename}`
- Uploads to S3 with content type
- Stores S3 URI in database: `s3://bucket/key`

Key changes:
```python
# Generate S3 key
s3_key = f"{settings.s3_prefix}{file_id}_{file.filename}"

# Upload to S3
s3_uri = storage.upload_bytes(
    key=s3_key,
    data=content,
    content_type=file.content_type,
)

# Store S3 URI in database
document = metadata_repo.create_document(
    filename=file.filename,
    file_path=s3_uri,  # Now stores s3://bucket/key
    format=file_ext,
    file_size_bytes=file_size,
)
```

### ✅ 5. Document Processing (`app/services/document_processor.py`)

**Before:**
- Loaded documents directly from local filesystem

**After:**
- Detects S3 URIs (`s3://`)
- Downloads to temporary file for processing
- Automatically cleans up temp files
- Backward compatible with local paths

Key changes:
```python
def load_document(self, file_path: str, format: str) -> List[dict]:
    if file_path.startswith("s3://"):
        # Extract S3 key
        s3_key = self.storage.extract_key_from_uri(file_path)
        
        # Download to temp file
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{format}", dir=self.settings.temp_dir
        )
        local_file_path = temp_file.name
        temp_file.close()
        
        self.storage.download_to_path(s3_key, local_file_path)
        
        # ... process document ...
        
    finally:
        # Cleanup temp file
        if temp_file and os.path.exists(local_file_path):
            os.unlink(local_file_path)
```

### ✅ 6. Dependencies (`requirements.txt`)

Added boto3:
```
# AWS
boto3>=1.34.0
```

### ✅ 7. Documentation

Created comprehensive documentation:
- `S3_INTEGRATION.md` - Full integration guide
- `S3_IMPLEMENTATION_SUMMARY.md` - This file
- `.env.example` cannot be created (blocked by .gitignore) but documented in guides

## File Structure

```
microservice/
├── app/
│   ├── api/
│   │   ├── dependencies.py          # ✏️ Modified - Added storage service
│   │   └── routes/
│   │       └── documents.py         # ✏️ Modified - S3 upload
│   ├── core/
│   │   └── config.py               # ✏️ Modified - AWS settings
│   ├── services/
│   │   ├── document_processor.py   # ✏️ Modified - S3 download
│   │   └── storage/                # 🆕 New
│   │       ├── __init__.py         # 🆕 New
│   │       ├── base.py             # 🆕 New - Interface
│   │       └── s3_storage.py       # 🆕 New - Implementation
├── requirements.txt                 # ✏️ Modified - Added boto3
├── S3_INTEGRATION.md               # 🆕 New - User guide
└── S3_IMPLEMENTATION_SUMMARY.md    # 🆕 New - This file
```

## Environment Variables Required

**Minimum required:**
```bash
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name
```

**Optional (for explicit credentials):**
```bash
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_SESSION_TOKEN=xxx
S3_ENDPOINT_URL=http://localhost:4566  # For LocalStack
S3_PREFIX=documents/
USE_S3_STORAGE=true
```

## Testing Checklist

Before deploying, test:

- [ ] Upload document - File appears in S3
- [ ] Process document - Downloads from S3 successfully
- [ ] Vectorize document - Works with S3-stored documents
- [ ] Generate mindmap - Works with S3-stored documents
- [ ] Error handling - Invalid credentials fail gracefully
- [ ] Temp file cleanup - No leftover files in temp directory
- [ ] Large files - Files near max size upload correctly
- [ ] Special characters - Filenames with spaces/unicode work

## Deployment Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create S3 bucket:**
   ```bash
   aws s3 mb s3://your-bucket-name --region us-east-1
   ```

3. **Set IAM permissions** (see S3_INTEGRATION.md)

4. **Update .env file:**
   ```bash
   AWS_REGION=us-east-1
   S3_BUCKET=your-bucket-name
   ```

5. **Test locally** (optional - use LocalStack):
   ```bash
   docker run -d -p 4566:4566 localstack/localstack
   aws --endpoint-url=http://localhost:4566 s3 mb s3://test-bucket
   # Set S3_ENDPOINT_URL=http://localhost:4566 in .env
   ```

6. **Deploy application**

7. **Verify upload:** Check S3 console for uploaded files

## No Database Migration Needed

The existing `file_path` column in the `documents` table already stores strings and can hold S3 URIs without any schema changes. Format changed from:
- **Before:** `./uploads/uuid_filename.pdf`
- **After:** `s3://bucket/documents/uuid_filename.pdf`

## Backward Compatibility

The `DocumentProcessorService.load_document()` method maintains backward compatibility:
- Detects S3 URIs with `startswith("s3://")`
- Falls back to local file loading for non-S3 paths
- Existing local files can still be processed (useful for migration)

## Benefits

1. **Scalable Storage** - No local disk constraints
2. **Durability** - S3 provides 99.999999999% durability
3. **Centralized** - Storage logic in one place, reusable by all services
4. **Flexible** - Easy to add CloudFront, presigned URLs, lifecycle policies
5. **Environment Agnostic** - Works with LocalStack for local dev
6. **Security** - Supports IAM roles, encryption, access logging

## Future Services Can Use Storage Layer

Any new service can inject `StorageService`:

```python
from app.api.dependencies import get_storage_service
from app.services.storage import StorageService
from fastapi import Depends

@router.post("/my-endpoint")
async def my_endpoint(storage: StorageService = Depends(get_storage_service)):
    # Upload
    uri = storage.upload_bytes("my-files/data.json", json_bytes)
    
    # Download
    storage.download_to_path("my-files/data.json", "/tmp/data.json")
    
    # Delete
    storage.delete("my-files/data.json")
```

## Potential Extensions

1. **LocalStorageService** - For local development without AWS
2. **Presigned URLs** - Direct client uploads/downloads
3. **Azure Blob Storage** - Alternative cloud provider
4. **GCS Storage** - Google Cloud Storage
5. **File versioning** - Keep document history
6. **Streaming uploads** - For very large files
7. **Compression** - Automatic compression before upload

## Key Design Decisions

1. **Storage URI in database** - Keeps database portable, no hardcoded buckets
2. **Temp file for processing** - LangChain loaders require local files
3. **Dependency injection** - Makes testing and swapping implementations easy
4. **Abstract interface** - Allows future storage backends without changing consumers
5. **S3 key format** - `documents/{uuid}_{filename}` balances uniqueness and readability
6. **Automatic cleanup** - Finally blocks ensure temp files are removed

## Support

For implementation questions, see:
- `S3_INTEGRATION.md` - Full integration guide with troubleshooting
- `app/services/storage/` - Storage service code
- `app/api/routes/documents.py` - Upload implementation
- `app/services/document_processor.py` - Processing implementation

