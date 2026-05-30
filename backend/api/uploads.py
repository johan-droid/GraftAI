import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from backend.auth.schemes import get_current_user_id

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/uploads", tags=["uploads"])
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "application/pdf", "text/plain", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
UPLOAD_DIR.mkdir(exist_ok=True)
MAGIC_BYTES: dict[str, bytes] = {"image/jpeg": b"\xff\xd8\xff", "image/png": b"\x89PNG", "image/gif": b"GIF8", "image/webp": b"RIFF", "application/pdf": b"%PDF"}

def _verify_magic_bytes(header_bytes: bytes, declared_content_type: str) -> bool:
    """Checks the start of the file against known magic bytes for the declared type."""
    expected_prefix = MAGIC_BYTES.get(declared_content_type)
    if expected_prefix is None:
        return True
    return header_bytes.startswith(expected_prefix)

@router.post("")
async def upload_file(file: UploadFile=File(...), user_id: str=Depends(get_current_user_id)):
    """
    Secure file upload endpoint.
    - Validates file size
    - Validates MIME type
    - Sanitizes filename via UUID generation
    - Stores in a dedicated non-executable directory
    """
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"File type {file.content_type} not allowed.")
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB.")
    file.file.seek(0)
    header_sample = file.file.read(16)
    file.file.seek(0)
    if not _verify_magic_bytes(header_sample, file.content_type):
        logger.warning("SEC-08: File magic byte mismatch for %s", file.content_type)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File content does not match the declared extension/type.")
    from backend.services.storage import storage
    extension = Path(file.filename).suffix or ".dat"
    secure_filename = f"{uuid.uuid4()}{extension}"
    remote_path = f"{user_id}/{secure_filename}"
    try:
        file.file.seek(0)
        upload_key = await storage.upload_file(file.file, remote_path, file.content_type)
        if not upload_key:
            msg = "Storage service rejected upload"
            raise Exception(msg)
    except Exception as e:
        logger.exception("Upload failed for user %s: %s", user_id, e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not save file to storage service.")
    access_url = storage.get_presigned_url(upload_key)
    return {"filename": secure_filename, "content_type": file.content_type, "size": file_size, "key": upload_key, "url": access_url}
