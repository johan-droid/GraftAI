import os
import logging
import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO

logger = logging.getLogger(__name__)

class StorageService:
    """
    S3/Cloudflare R2 Compatible Storage Service.
    Handles document uploads and retrieval for the GraftAI platform.
    """
    def __init__(self):
        self.bucket = os.getenv("STORAGE_S3_BUCKET")
        self.endpoint = os.getenv("STORAGE_S3_ENDPOINT")
        self.access_key = os.getenv("STORAGE_S3_ACCESS_KEY")
        self.secret_key = os.getenv("STORAGE_S3_SECRET_KEY")
        self.region = os.getenv("STORAGE_S3_REGION", "auto")
        
        # Initialize client if configured
        if all([self.bucket, self.access_key, self.secret_key]):
            self.client = boto3.client(
                's3',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                endpoint_url=self.endpoint,
                region_name=self.region
            )
            logger.info(f"✅ Storage Service initialized for bucket: {self.bucket}")
        else:
            self.client = None
            logger.warning("⚠️ Cloud Storage NOT configured. Falling back to temporary local storage.")

    async def upload_file(self, file_obj: BinaryIO, remote_path: str, content_type: str) -> Optional[str]:
        """Uploads a file to the cloud bucket and returns the object key."""
        if not self.client:
            # Local fallback for development (statelessness not guaranteed)
            local_path = os.path.join("uploads", remote_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(file_obj.read())
            return local_path

        try:
            self.client.upload_fileobj(
                file_obj,
                self.bucket,
                remote_path,
                ExtraArgs={'ContentType': content_type}
            )
            logger.info(f"✅ Successfully uploaded {remote_path} to Cloud Storage.")
            return remote_path
        except ClientError as e:
            logger.error(f"❌ Cloud Upload ERROR: {e}")
            return None

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> Optional[str]:
        """Generates a secure, time-limited URL for document retrieval."""
        if not self.client:
            return f"/api/v1/uploads/local/{key}"

        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            return None

    def delete_file(self, key: str) -> bool:
        """Deletes an object from the cloud bucket."""
        if not self.client:
            return False
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            logger.warning(f"⚠️ Failed to delete cloud artifact {key}: {e}")
            return False

    def get_presigned_upload_url(self, key: str, expires_in: int = 3600, content_type: str | None = None) -> Optional[dict]:
        """Generate a presigned upload URL (PUT) or return a backend fallback.

        Returns a dict with shape:
          - method: 'put' | 'backend'
          - upload_url: <url> (for 'put')
          - key: <object key>
          - access_url: <presigned-get-url> (optional)
          - upload_endpoint: '/api/v1/uploads' (for backend fallback)
        """
        if not self.client:
            # Local/dev fallback: instruct the frontend to POST to the backend upload endpoint
            return {
                "method": "backend",
                "upload_endpoint": "/api/v1/uploads",
                "key": key,
            }

        try:
            params = {"Bucket": self.bucket, "Key": key}
            if content_type:
                # When generating a PUT presign, including ContentType in Params will make
                # the presigned URL require that header on upload (recommended).
                params["ContentType"] = content_type

            url = self.client.generate_presigned_url(
                'put_object',
                Params=params,
                ExpiresIn=expires_in,
            )

            access_url = self.get_presigned_url(key, expires_in=expires_in)
            result = {
                "method": "put",
                "upload_url": url,
                "key": key,
            }
            if access_url is not None:
                result["access_url"] = access_url

            return result
        except ClientError as e:
            logger.error(f"❌ Failed to generate presigned upload URL: {e}")
            return None

# Export singleton
storage = StorageService()
