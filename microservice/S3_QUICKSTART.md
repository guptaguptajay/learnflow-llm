# S3 Storage - Quick Start Guide

## 1. Install Dependencies

```bash
cd microservice
pip install -r requirements.txt
```

## 2. Create S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://your-bucket-name --region us-east-1

# Or use AWS Console
# https://s3.console.aws.amazon.com/s3/buckets
```

## 3. Configure Environment

Add to your `.env` file:

```bash
# Required
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name

# Optional (if not using IAM roles)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

## 4. Set IAM Permissions

Your AWS user/role needs these S3 permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::your-bucket-name/documents/*"
    }
  ]
}
```

## 5. Test It

```bash
# Start the service
python -m app.main

# Upload a document
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@test.pdf"

# Check S3
aws s3 ls s3://your-bucket-name/documents/
```

## Local Development (Without AWS)

Use LocalStack for local testing:

```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Create bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://test-bucket

# Update .env
S3_BUCKET=test-bucket
S3_ENDPOINT_URL=http://localhost:4566
AWS_REGION=us-east-1
```

## How It Works

1. **Upload:** Files go directly to S3, URI stored in database
2. **Process:** Service downloads from S3 to temp, processes, cleans up
3. **Storage:** `file_path` in DB = `s3://bucket/documents/uuid_filename.pdf`

## Common Issues

### "Failed to upload to S3"
- Check AWS credentials: `aws sts get-caller-identity`
- Verify bucket exists: `aws s3 ls s3://your-bucket-name`
- Check region matches

### "Access Denied"
- Review IAM permissions
- Ensure credentials have PutObject/GetObject rights

### "Bucket not found"
- Create bucket: `aws s3 mb s3://your-bucket-name`
- Check S3_BUCKET env var matches

## Using in Other Services

```python
from app.services.storage import StorageService
from app.api.dependencies import get_storage_service
from fastapi import Depends

@router.post("/my-endpoint")
async def my_endpoint(storage: StorageService = Depends(get_storage_service)):
    # Upload
    uri = storage.upload_bytes("path/file.txt", data, "text/plain")
    
    # Download
    storage.download_to_path("path/file.txt", "/tmp/file.txt")
    
    # Delete
    storage.delete("path/file.txt")
```

## Files Changed

- ✅ `app/core/config.py` - AWS config
- ✅ `app/services/storage/` - New storage layer
- ✅ `app/api/dependencies.py` - Storage DI
- ✅ `app/api/routes/documents.py` - S3 upload
- ✅ `app/services/document_processor.py` - S3 download
- ✅ `requirements.txt` - boto3 added

## More Info

- Full guide: `S3_INTEGRATION.md`
- Implementation details: `S3_IMPLEMENTATION_SUMMARY.md`

