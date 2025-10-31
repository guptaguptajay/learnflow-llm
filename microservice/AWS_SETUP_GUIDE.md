# AWS Setup Guide for LearnFlow

## Your Configuration

```bash
AWS_REGION=ap-south-2
S3_BUCKET=learnflow-documents
```

---

## Step 1: Create S3 Bucket

### Option A: Using AWS Console

1. Go to https://s3.console.aws.amazon.com/s3/buckets
2. Click "Create bucket"
3. **Bucket name:** `learnflow-documents`
4. **AWS Region:** Asia Pacific (Hyderabad) `ap-south-2`
5. **Block Public Access:** Keep all checked (recommended)
6. Click "Create bucket"

### Option B: Using AWS CLI

```bash
aws s3 mb s3://learnflow-documents --region ap-south-2
```

---

## Step 2: Create IAM User (For Development)

### Using AWS Console:

1. **Go to IAM Console**
   - https://console.aws.amazon.com/iam/

2. **Create User**
   - Click "Users" → "Create user"
   - User name: `learnflow-service`
   - Click "Next"

3. **Set Permissions**
   - Select "Attach policies directly"
   - Click "Create policy" (opens new tab)
   - Switch to "JSON" tab
   - Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LearnFlowS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::learnflow-documents",
        "arn:aws:s3:::learnflow-documents/*"
      ]
    }
  ]
}
```

   - Click "Next"
   - Policy name: `LearnFlowS3Policy`
   - Click "Create policy"
   - Go back to user creation tab, refresh policies
   - Search for "LearnFlowS3Policy" and select it
   - Click "Next" → "Create user"

4. **Create Access Key**
   - Click on the user you just created
   - Go to "Security credentials" tab
   - Scroll to "Access keys"
   - Click "Create access key"
   - Select "Application running outside AWS"
   - Click "Next" → "Create access key"
   - **IMPORTANT:** Copy both keys immediately:
     - Access Key ID (starts with AKIA...)
     - Secret Access Key (long string, shown only once)
   - Click "Download .csv" (backup)
   - Click "Done"

---

## Step 3: Configure Your Application

### Update .env file:

```bash
# Application Settings
APP_NAME=GenAI Document Mapping Service
DEBUG=false
LOG_LEVEL=INFO

# PostgreSQL Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=document_mapping
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# OpenAI Settings
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-large
OPENAI_EMBEDDING_DIMENSIONS=3072

# LLM Provider
LLM_PROVIDER=openai

# Document Processing
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_FILE_SIZE_MB=50

# Temp Directory (needed for processing)
TEMP_DIR=./temp

# AWS S3 Configuration
AWS_REGION=ap-south-2
S3_BUCKET=learnflow-documents
S3_PREFIX=documents/
USE_S3_STORAGE=true

# AWS Credentials (from Step 2)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## Step 4: Test Connection

Create a test script to verify AWS connection:

```bash
cd microservice
python -c "
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# Test connection
s3 = boto3.client('s3', region_name=os.getenv('AWS_REGION'))
response = s3.list_buckets()
print('✅ AWS Connection Successful!')
print('Available buckets:', [b['Name'] for b in response['Buckets']])

# Test bucket access
bucket = os.getenv('S3_BUCKET')
try:
    s3.head_bucket(Bucket=bucket)
    print(f'✅ Bucket {bucket} is accessible!')
except Exception as e:
    print(f'❌ Cannot access bucket {bucket}: {e}')
"
```

---

## Alternative: Using AWS CLI Configuration

If you prefer not to put credentials in `.env`:

1. **Install AWS CLI**
   ```bash
   pip install awscli
   ```

2. **Configure AWS CLI**
   ```bash
   aws configure
   ```
   
   Enter:
   - AWS Access Key ID: `AKIA...`
   - AWS Secret Access Key: `secret...`
   - Default region: `ap-south-2`
   - Default output format: `json`

3. **Test**
   ```bash
   aws s3 ls s3://learnflow-documents
   ```

4. **Update .env** (no credentials needed)
   ```bash
   AWS_REGION=ap-south-2
   S3_BUCKET=learnflow-documents
   S3_PREFIX=documents/
   USE_S3_STORAGE=true
   # AWS credentials will be read from ~/.aws/credentials
   ```

---

## Production Deployment on AWS (EC2/ECS)

For production on AWS, use IAM Roles instead of access keys:

### For EC2 Instance:

1. **Create IAM Role**
   - Go to IAM → Roles → Create role
   - Trusted entity: AWS service → EC2
   - Attach `LearnFlowS3Policy` (created earlier)
   - Role name: `LearnFlowEC2Role`
   - Create role

2. **Attach to EC2**
   - Go to EC2 console
   - Select your instance
   - Actions → Security → Modify IAM role
   - Select `LearnFlowEC2Role`

3. **Update .env** (no credentials needed!)
   ```bash
   AWS_REGION=ap-south-2
   S3_BUCKET=learnflow-documents
   # No AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY needed!
   ```

### For ECS/Fargate:

1. Create Task Execution Role with S3 policy attached
2. Assign to your ECS task definition
3. No credentials in environment variables

### For Lambda:

1. Lambda execution role automatically gets credentials
2. Just attach S3 policy to the role

---

## Security Best Practices

### ✅ DO:
- Use IAM roles when running on AWS
- Rotate access keys regularly (every 90 days)
- Use separate users/roles for dev/staging/prod
- Enable CloudTrail for audit logging
- Use AWS Secrets Manager for sensitive data
- Enable S3 bucket versioning
- Enable S3 server-side encryption

### ❌ DON'T:
- Commit `.env` file to git (already in .gitignore)
- Share access keys via email/Slack
- Use root account credentials
- Give broader permissions than needed
- Disable public access blocks on S3

---

## Troubleshooting

### Error: "The specified bucket does not exist"
```bash
# Create bucket
aws s3 mb s3://learnflow-documents --region ap-south-2
```

### Error: "Access Denied"
```bash
# Check IAM policy is attached
aws iam list-attached-user-policies --user-name learnflow-service

# Verify credentials
aws sts get-caller-identity
```

### Error: "Invalid AWS credentials"
```bash
# Test credentials
aws s3 ls --region ap-south-2

# If fails, reconfigure
aws configure
```

### Error: "Could not connect to endpoint"
```bash
# Check region is correct
echo $AWS_REGION  # Should be ap-south-2

# Verify endpoint
aws s3 ls --region ap-south-2 --debug
```

---

## Cost Estimation

### S3 Storage (ap-south-2 pricing):
- **Storage:** ₹1.84/GB/month (~$0.022/GB)
- **PUT requests:** ₹0.037 per 1,000 requests
- **GET requests:** ₹0.003 per 1,000 requests

### Example Usage:
- 1,000 documents @ 5MB each = 5GB
- Cost: ~₹9.20/month (~$0.11/month)
- Very affordable! 💰

### Free Tier (first 12 months):
- 5GB storage
- 20,000 GET requests
- 2,000 PUT requests

---

## Next Steps

1. ✅ Create S3 bucket: `learnflow-documents`
2. ✅ Create IAM user: `learnflow-service`
3. ✅ Create access keys
4. ✅ Update `.env` file
5. ✅ Test connection (run test script above)
6. ✅ Start your application
7. ✅ Upload a test document
8. ✅ Verify file in S3 console

---

## Quick Commands Reference

```bash
# List bucket contents
aws s3 ls s3://learnflow-documents/documents/ --region ap-south-2

# Check bucket size
aws s3 ls s3://learnflow-documents --recursive --summarize --region ap-south-2

# Download a file
aws s3 cp s3://learnflow-documents/documents/uuid_file.pdf ./local.pdf --region ap-south-2

# Delete a file
aws s3 rm s3://learnflow-documents/documents/uuid_file.pdf --region ap-south-2

# Verify IAM identity
aws sts get-caller-identity

# Test S3 access
aws s3api head-bucket --bucket learnflow-documents --region ap-south-2
```

---

## Support

If you encounter issues:
1. Check CloudWatch Logs (if on AWS)
2. Check application logs (set `LOG_LEVEL=DEBUG` in .env)
3. Verify IAM permissions
4. Test AWS CLI access separately

For detailed integration info, see: `S3_INTEGRATION.md`

