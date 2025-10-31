# S3 Storage Integration Guide

This document describes the S3 storage integration that replaces local file storage for uploaded documents.

## Overview

Documents are now uploaded to AWS S3 instead of being stored locally. The system uses a centralized storage service layer that can be reused by other services in the application.

## Architecture

### Storage Service Layer

A new abstraction layer has been added at `app/services/storage/`:

```
app/services/storage/
├── __init__.py          # Exports StorageService and S3StorageService
├── base.py              # Abstract StorageService interface
└── s3_storage.py        # S3 implementation
```

**Key Methods:**
- `upload_bytes(key, data, content_type)` - Upload bytes to S3
- `download_to_path(key, dest_path)` - Download S3 object to local file
- `get_uri(key)` - Get S3 URI (s3://bucket/key)
- `delete(key)` - Delete object from S3
- `extract_key_from_uri(uri)` - Extract S3 key from URI

### Storage Key Format

Documents are stored using the agreed format:
```
documents/{uuid}_{original_filename}
```

Example: `documents/a1b2c3d4-e5f6-7890-abcd-ef1234567890_mybook.pdf`

### Database Storage

The `file_path` field in the database now stores the full S3 URI:
```
s3://your-bucket-name/documents/a1b2c3d4-e5f6-7890-abcd-ef1234567890_mybook.pdf
```

No database migrations are needed since `file_path` is already a string column.

## Configuration

### Required Environment Variables

Add these to your `.env` file:

```bash
# AWS/S3 Settings
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name-here
S3_PREFIX=documents/
USE_S3_STORAGE=true
```

### Optional Environment Variables

```bash
# AWS Credentials (optional - can use IAM roles or ~/.aws/credentials)
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_SESSION_TOKEN=your_session_token_here  # For temporary credentials

# S3 Endpoint URL (for LocalStack, MinIO, or custom S3-compatible storage)
S3_ENDPOINT_URL=http://localhost:4566
```

### AWS Credentials Priority

The S3 client will use credentials in this order:
1. Explicit credentials from environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS credentials file (`~/.aws/credentials`)
3. IAM role (when running on EC2, ECS, Lambda, etc.)
4. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)

For production, **IAM roles are recommended** for better security.

## Dependencies

The following dependency has been added to `requirements.txt`:

```
boto3>=1.34.0
```

Install with:
```bash
pip install -r requirements.txt
```

## Usage Flow

### 1. Document Upload

**Endpoint:** `POST /documents/upload`

**Flow:**
1. Client uploads file via multipart/form-data
2. Server validates file format and size
3. Generates UUID and constructs S3 key: `documents/{uuid}_{filename}`
4. Uploads file bytes to S3 with content type
5. Stores S3 URI (`s3://bucket/key`) in database `file_path` field
6. Returns document metadata to client

**Code Location:** `app/api/routes/documents.py:upload_document()`

### 2. Document Processing

**Endpoint:** `POST /documents/process`

**Flow:**
1. Client requests processing with document_id
2. Server retrieves document record from database (contains S3 URI)
3. `DocumentProcessorService.load_document()` detects S3 URI
4. Downloads file to temporary location
5. Processes document (extracts text, creates chunks)
6. Cleans up temporary file
7. Stores chunks in database

**Code Location:** `app/services/document_processor.py:load_document()`

### 3. Automatic Cleanup

Temporary files are automatically cleaned up using a `finally` block to ensure resources are freed even if processing fails.

## Integration with Other Services

Other services can use the storage layer by injecting `StorageService`:

```python
from app.api.dependencies import get_storage_service
from app.services.storage import StorageService

def my_service_function(storage: StorageService = Depends(get_storage_service)):
    # Upload a file
    uri = storage.upload_bytes("my-key", data, "application/pdf")
    
    # Download a file
    storage.download_to_path("my-key", "/tmp/local-file.pdf")
    
    # Delete a file
    storage.delete("my-key")
```

## Testing with LocalStack

For local development without AWS, use LocalStack:

```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Create bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://your-bucket-name

# Set environment variable
S3_ENDPOINT_URL=http://localhost:4566
```

## AWS Permissions

The IAM user/role needs these S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/documents/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name"
    }
  ]
}
```

## Troubleshooting

### Issue: "Failed to upload to S3"

**Possible causes:**
- Invalid AWS credentials
- Bucket doesn't exist
- Insufficient permissions
- Network connectivity issues

**Solutions:**
1. Verify credentials: `aws s3 ls s3://your-bucket-name`
2. Check bucket exists and region is correct
3. Review IAM permissions
4. Check network/firewall rules

### Issue: "Failed to download from S3"

**Possible causes:**
- File doesn't exist in S3
- Insufficient read permissions
- Network issues

**Solutions:**
1. Verify file exists: `aws s3 ls s3://your-bucket-name/documents/`
2. Check IAM read permissions
3. Verify S3 URI format in database

### Issue: Temp directory issues

**Possible causes:**
- Temp directory doesn't exist
- Insufficient disk space
- Permission issues

**Solutions:**
1. Ensure `TEMP_DIR` exists: `mkdir -p ./temp`
2. Check disk space: `df -h`
3. Verify write permissions

## Migration from Local Storage

If you have existing documents stored locally:

1. **Upload existing files to S3:**
```python
# migration_script.py
import os
from app.core.config import get_settings
from app.services.storage import S3StorageService
from app.repositories.metadata_store import MetadataRepository

settings = get_settings()
storage = S3StorageService(settings.s3_bucket_name, settings.aws_region)
repo = MetadataRepository()

# Get all documents
documents = repo.get_session().query(Document).all()

for doc in documents:
    if not doc.file_path.startswith("s3://"):
        # Read local file
        with open(doc.file_path, "rb") as f:
            data = f.read()
        
        # Upload to S3
        key = f"{settings.s3_prefix}{os.path.basename(doc.file_path)}"
        s3_uri = storage.upload_bytes(key, data)
        
        # Update database
        doc.file_path = s3_uri
        repo.get_session().commit()
        
        print(f"Migrated: {doc.filename} -> {s3_uri}")
```

2. **Run the migration script**
3. **Verify all documents are accessible**
4. **Delete local files** (after verification)

## Future Enhancements

Potential improvements:

1. **Presigned URLs** - Generate temporary URLs for direct client downloads
2. **Multipart uploads** - For large files >5GB
3. **S3 lifecycle policies** - Automatic archival/deletion
4. **CloudFront CDN** - Faster global distribution
5. **Local storage fallback** - For development without AWS
6. **File versioning** - Keep multiple versions of documents
7. **Encryption at rest** - Server-side encryption (SSE-S3 or SSE-KMS)

## Code Changes Summary

### New Files
- `app/services/storage/__init__.py`
- `app/services/storage/base.py`
- `app/services/storage/s3_storage.py`

### Modified Files
- `app/core/config.py` - Added AWS/S3 settings
- `app/api/dependencies.py` - Added storage service provider
- `app/api/routes/documents.py` - Updated upload to use S3
- `app/services/document_processor.py` - Updated to download from S3
- `requirements.txt` - Added boto3

### Configuration Files
- `.env` (create from `.env.example`) - Add AWS credentials and bucket

## Support

For issues or questions about S3 integration, check:
1. CloudWatch logs (if running on AWS)
2. Application logs (`LOG_LEVEL=DEBUG` for verbose output)
3. AWS S3 console for bucket/object inspection
4. IAM console for permission verification

