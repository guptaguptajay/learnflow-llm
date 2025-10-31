#!/usr/bin/env python3
"""Test script to verify AWS S3 connection and configuration."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.services.storage import S3StorageService


def test_aws_connection():
    """Test AWS S3 connection and basic operations."""
    print("=" * 70)
    print("LearnFlow S3 Connection Test")
    print("=" * 70)
    
    # Load settings
    print("\n1️⃣  Loading configuration...")
    settings = get_settings()
    
    print(f"   ✓ AWS Region: {settings.aws_region}")
    print(f"   ✓ S3 Bucket: {settings.s3_bucket_name}")
    print(f"   ✓ S3 Prefix: {settings.s3_prefix}")
    
    if settings.aws_access_key_id:
        print(f"   ✓ Access Key ID: {settings.aws_access_key_id[:10]}...")
    else:
        print("   ℹ Using IAM role or AWS CLI credentials")
    
    if not settings.s3_bucket_name:
        print("\n❌ ERROR: S3_BUCKET not configured in .env")
        print("   Please add: S3_BUCKET=learnflow-documents")
        return False
    
    # Initialize storage service
    print("\n2️⃣  Initializing S3 storage service...")
    try:
        storage = S3StorageService(
            bucket=settings.s3_bucket_name,
            region=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.aws_access_key_id,
            secret_access_key=settings.aws_secret_access_key,
            session_token=settings.aws_session_token,
        )
        print("   ✓ Storage service initialized")
    except Exception as e:
        print(f"\n❌ ERROR: Failed to initialize storage service")
        print(f"   {str(e)}")
        return False
    
    # Test 1: Check if bucket exists
    print("\n3️⃣  Testing bucket access...")
    try:
        storage.client.head_bucket(Bucket=settings.s3_bucket_name)
        print(f"   ✓ Bucket '{settings.s3_bucket_name}' is accessible")
    except Exception as e:
        print(f"\n❌ ERROR: Cannot access bucket '{settings.s3_bucket_name}'")
        print(f"   {str(e)}")
        print("\n   Possible solutions:")
        print("   - Create bucket: aws s3 mb s3://learnflow-documents --region ap-south-2")
        print("   - Check IAM permissions (PutObject, GetObject, ListBucket)")
        print("   - Verify AWS credentials are correct")
        return False
    
    # Test 2: Upload a test file
    print("\n4️⃣  Testing upload...")
    test_data = b"LearnFlow S3 Test - Connection Successful!"
    test_key = f"{settings.s3_prefix}test/connection_test.txt"
    
    try:
        uri = storage.upload_bytes(test_key, test_data, "text/plain")
        print(f"   ✓ Upload successful: {uri}")
    except Exception as e:
        print(f"\n❌ ERROR: Upload failed")
        print(f"   {str(e)}")
        print("\n   Check IAM permissions include: s3:PutObject")
        return False
    
    # Test 3: Download the file
    print("\n5️⃣  Testing download...")
    import tempfile
    import os
    
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
        temp_path = temp_file.name
        temp_file.close()
        
        storage.download_to_path(test_key, temp_path)
        
        with open(temp_path, "rb") as f:
            downloaded_data = f.read()
        
        os.unlink(temp_path)
        
        if downloaded_data == test_data:
            print(f"   ✓ Download successful and content matches")
        else:
            print(f"   ⚠ Download successful but content mismatch")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: Download failed")
        print(f"   {str(e)}")
        print("\n   Check IAM permissions include: s3:GetObject")
        return False
    
    # Test 4: Delete the test file
    print("\n6️⃣  Testing delete...")
    try:
        storage.delete(test_key)
        print(f"   ✓ Delete successful")
    except Exception as e:
        print(f"\n❌ ERROR: Delete failed")
        print(f"   {str(e)}")
        print("\n   Check IAM permissions include: s3:DeleteObject")
        return False
    
    # Success!
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED!")
    print("=" * 70)
    print("\nYour S3 integration is configured correctly.")
    print("You can now upload documents to LearnFlow.\n")
    
    return True


if __name__ == "__main__":
    try:
        success = test_aws_connection()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

