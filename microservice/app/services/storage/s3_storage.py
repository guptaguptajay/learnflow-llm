"""S3 storage service implementation."""

import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.core.logging import get_logger
from app.services.storage.base import StorageService

logger = get_logger(__name__)


class S3StorageService(StorageService):
    """S3-backed storage service."""

    def __init__(
        self,
        bucket: str,
        region: str,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        session_token: Optional[str] = None,
    ):
        """Initialize S3 storage service.

        Args:
            bucket: S3 bucket name
            region: AWS region
            endpoint_url: Optional custom endpoint (for LocalStack, MinIO, etc.)
            access_key_id: Optional AWS access key ID
            secret_access_key: Optional AWS secret access key
            session_token: Optional AWS session token
        """
        self.bucket = bucket
        self.region = region

        # Build boto3 client kwargs
        client_kwargs = {"region_name": region}
        
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url
        
        if access_key_id and secret_access_key:
            client_kwargs["aws_access_key_id"] = access_key_id
            client_kwargs["aws_secret_access_key"] = secret_access_key
            
        if session_token:
            client_kwargs["aws_session_token"] = session_token

        self.client = boto3.client("s3", **client_kwargs)
        logger.info(f"Initialized S3 storage: bucket={bucket}, region={region}")

    def upload_bytes(self, key: str, data: bytes, content_type: Optional[str] = None) -> str:
        """Upload bytes to S3.

        Args:
            key: S3 key
            data: Binary data to upload
            content_type: Optional MIME type

        Returns:
            S3 URI (s3://bucket/key)

        Raises:
            Exception: If upload fails
        """
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, **extra_args)
            
            uri = self.get_uri(key)
            logger.info(f"Uploaded to S3: {uri} ({len(data)} bytes)")
            return uri

        except ClientError as e:
            logger.error(f"S3 upload failed for key {key}: {str(e)}")
            raise Exception(f"Failed to upload to S3: {str(e)}") from e

    def download_to_path(self, key: str, dest_path: str) -> None:
        """Download S3 object to local file.

        Args:
            key: S3 key
            dest_path: Local destination path

        Raises:
            Exception: If download fails
        """
        try:
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest_path) or ".", exist_ok=True)

            self.client.download_file(self.bucket, key, dest_path)
            logger.info(f"Downloaded from S3: {key} -> {dest_path}")

        except ClientError as e:
            logger.error(f"S3 download failed for key {key}: {str(e)}")
            raise Exception(f"Failed to download from S3: {str(e)}") from e

    def get_uri(self, key: str) -> str:
        """Get S3 URI for a key.

        Args:
            key: S3 key

        Returns:
            S3 URI (s3://bucket/key)
        """
        return f"s3://{self.bucket}/{key}"

    def delete(self, key: str) -> None:
        """Delete object from S3.

        Args:
            key: S3 key

        Raises:
            Exception: If deletion fails
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            logger.info(f"Deleted from S3: {key}")

        except ClientError as e:
            logger.error(f"S3 deletion failed for key {key}: {str(e)}")
            raise Exception(f"Failed to delete from S3: {str(e)}") from e

    def extract_key_from_uri(self, uri: str) -> str:
        """Extract S3 key from URI.

        Args:
            uri: S3 URI (s3://bucket/key)

        Returns:
            S3 key

        Raises:
            ValueError: If URI format is invalid
        """
        if not uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI: {uri}")

        # Remove s3:// prefix and bucket name
        parts = uri[5:].split("/", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {uri}")

        bucket, key = parts
        if bucket != self.bucket:
            raise ValueError(f"URI bucket {bucket} doesn't match configured bucket {self.bucket}")

        return key

