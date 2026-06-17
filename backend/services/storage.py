import asyncio
import logging
import os
from typing import BinaryIO
from urllib.parse import quote

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def _safe_path(base_dir: str, remote_path: str) -> str:
    base_dir = os.path.abspath(base_dir)
    candidate_path = os.path.abspath(os.path.join(base_dir, remote_path))
    if os.path.commonpath([base_dir, candidate_path]) != base_dir:
        msg = f"Invalid remote path: {remote_path}"
        raise ValueError(msg)
    return candidate_path

def _sync_upload(file_obj: BinaryIO, local_path: str) -> None:
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(file_obj.read())

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
        if all([self.bucket, self.access_key, self.secret_key]):
            self._client_sync = boto3.client("s3", aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key, endpoint_url=self.endpoint, region_name=self.region)
            logger.info(" Storage Service initialized for bucket: %s", self.bucket)
        else:
            self._client_sync = None
            logger.warning(" Cloud Storage NOT configured. Falling back to temporary local storage.")

    async def upload_file(self, file_obj: BinaryIO, remote_path: str, content_type: str) -> str | None:
        """Uploads a file to the cloud bucket and returns the object key."""
        if not self._client_sync:
            local_path = _safe_path("uploads", remote_path)
            await asyncio.to_thread(_sync_upload, file_obj, local_path)
            return remote_path
        try:
            await asyncio.to_thread(self._client_sync.upload_fileobj, file_obj, self.bucket, remote_path, ExtraArgs={"ContentType": content_type})
            logger.info(" Successfully uploaded %s to Cloud Storage.", remote_path)
            return remote_path
        except ClientError as e:
            logger.exception(" Cloud Upload ERROR: %s", e)
            return None

    async def get_presigned_url(self, key: str, expires_in: int=3600) -> str | None:
        """Generates a secure, time-limited URL for document retrieval."""
        if not self._client_sync:
            encoded_key = quote(key, safe="/")
            return f"/api/v1/uploads/local/{encoded_key}"
        try:
            return await asyncio.to_thread(self._client_sync.generate_presigned_url, "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires_in)
        except ClientError as e:
            logger.exception(" Failed to generate presigned URL: %s", e)
            return None

    async def get_file_size(self, key: str) -> int:
        """Gets the file size of an object from the cloud bucket or local fallback path."""
        if not self._client_sync:
            try:
                local_path = _safe_path("uploads", key)
            except ValueError:
                return 0
            if os.path.exists(local_path):
                return os.path.getsize(local_path)
            return 0
        try:
            response = await asyncio.to_thread(self._client_sync.head_object, Bucket=self.bucket, Key=key)
            return response.get("ContentLength", 0)
        except ClientError as e:
            logger.warning(" Failed to get file size for %s: %s", key, e)
            return 0

    async def delete_file(self, key: str) -> bool:
        """Deletes an object from the cloud bucket or local fallback path."""
        if not self._client_sync:
            try:
                local_path = _safe_path("uploads", key)
            except ValueError:
                logger.warning("Attempted to delete invalid local storage path: %s", key)
                return False
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                    return True
                except OSError as exc:
                    logger.warning("Failed to delete local storage file %s: %s", key, exc)
            return False
        try:
            await asyncio.to_thread(self._client_sync.delete_object, Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            logger.warning(" Failed to delete cloud artifact %s: %s", key, e)
            return False

    async def get_presigned_upload_url(self, key: str, expires_in: int=3600, content_type: str | None=None) -> dict | None:
        """Generate a presigned upload URL (PUT) or return a backend fallback.

        Returns a dict with shape:
          - method: 'put' | 'backend'
          - upload_url: <url> (for 'put')
          - key: <object key>
          - access_url: <presigned-get-url> (optional)
          - upload_endpoint: '/api/v1/uploads' (for backend fallback)
        """
        if not self._client_sync:
            return {"method": "backend", "upload_endpoint": "/api/v1/uploads", "key": key}
        try:
            params = {"Bucket": self.bucket, "Key": key}
            if content_type:
                params["ContentType"] = content_type
            url = await asyncio.to_thread(self._client_sync.generate_presigned_url, "put_object", Params=params, ExpiresIn=expires_in)
            access_url = await self.get_presigned_url(key, expires_in=expires_in)
            result = {"method": "put", "upload_url": url, "key": key}
            if access_url is not None:
                result["access_url"] = access_url
            return result
        except ClientError as e:
            logger.exception(" Failed to generate presigned upload URL: %s", e)
            return None
storage = StorageService()
