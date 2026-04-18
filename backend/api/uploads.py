import os
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from backend.auth.schemes import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Configuration
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# Ensure upload directory exists and is not executable
UPLOAD_DIR.mkdir(exist_ok=True)
# On Unix-like systems, we'd set permissions here.
# On Windows, we ensure the directory is created.

# SEC-08 Magic Byte signatures for strict MIME validation
MAGIC_BYTES: dict[str, bytes] = {
    "image/jpeg": b"\xff\xd8\xff",
    "image/png": b"\x89PNG",
    "image/gif": b"GIF8",
    "image/webp": b"RIFF",
    "application/pdf": b"%PDF",
}


def _verify_magic_bytes(header_bytes: bytes, declared_content_type: str) -> bool:
    """Checks the start of the file against known magic bytes for the declared type."""
    expected_prefix = MAGIC_BYTES.get(declared_content_type)
    if expected_prefix is None:
        # Pass through for types we don't have binary signatures for (docx, txt, etc.)
        return True
    return header_bytes.startswith(expected_prefix)


@router.post("")
async def upload_file(
    file: UploadFile = File(...), user_id: str = Depends(get_current_user_id)
):
    """
    Secure file upload endpoint.
    - Validates file size
    - Validates MIME type
    - Sanitizes filename via UUID generation
    - Stores in a dedicated non-executable directory
    """
    # 1. Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed.",
        )

    # 2. Validate File Size & Magic Bytes (SEC-08)
    # - Check size by seeking
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB.",
        )

    # - Verify Magic Bytes
    file.file.seek(0)
    header_sample = file.file.read(16)
    file.file.seek(0)  # IMPORTANT: reset pointer for the storage service later

    if not _verify_magic_bytes(header_sample, file.content_type):
        logger.warning(f"SEC-08: File magic byte mismatch for {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match the declared extension/type.",
        )

    # 3. Generate Secure Filename (UUID)
    from backend.services.storage import storage

    extension = Path(file.filename).suffix or ".dat"
    secure_filename = f"{uuid.uuid4()}{extension}"
    remote_path = f"{user_id}/{secure_filename}"

    # 4. Save File via Storage Service (Cloud-Streaming)
    try:
        # We need to seek back to 0 just in case it was moved
        file.file.seek(0)
        upload_key = await storage.upload_file(
            file.file, remote_path, file.content_type
        )
        if not upload_key:
            raise Exception("Storage service rejected upload")
    except Exception as e:
        logger.error(f"Upload failed for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file to storage service.",
        )

    # 5. Generate secure retrieval URL
    access_url = storage.get_presigned_url(upload_key)

    return {
        "filename": secure_filename,
        "content_type": file.content_type,
        "size": file_size,
        "key": upload_key,
        "url": access_url,
    }
