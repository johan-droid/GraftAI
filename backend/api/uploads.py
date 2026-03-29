import os
import uuid
import shutil
import imghdr
from pathlib import Path
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from backend.auth.schemes import get_current_user_id
from backend.utils.tenant import get_current_org_id, get_current_workspace_id

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Configuration
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# MIME type to extension mapping for validation
MIME_TYPE_EXTENSIONS: Dict[str, List[str]] = {
    "image/jpeg": [".jpg", ".jpeg"],
    "image/png": [".png"],
    "image/gif": [".gif"],
    "image/webp": [".webp"],
    "application/pdf": [".pdf"],
    "text/plain": [".txt"],
    "application/msword": [".doc"],
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
}

ALLOWED_MIME_TYPES = set(MIME_TYPE_EXTENSIONS.keys())

def _validate_file_content(file: UploadFile, declared_mime: str) -> bool:
    """Validate file content matches declared MIME type using magic numbers."""
    # Read first few bytes for magic number detection
    header = file.file.read(8)
    file.file.seek(0)
    
    # Magic number signatures
    signatures = {
        b'\xff\xd8\xff': 'image/jpeg',  # JPEG
        b'\x89PNG\r\n\x1a\n': 'image/png',  # PNG
        b'GIF87a': 'image/gif',  # GIF
        b'GIF89a': 'image/gif',  # GIF
        b'RIFF': 'image/webp',  # WebP (starts with RIFF)
        b'%PDF': 'application/pdf',  # PDF
    }
    
    detected_type = None
    for sig, mime in signatures.items():
        if header.startswith(sig):
            detected_type = mime
            break
    
    # For text files, check if it's readable text
    if declared_mime == 'text/plain':
        try:
            sample = header.decode('utf-8', errors='strict')
            return True
        except UnicodeDecodeError:
            return False
    
    # For Office documents, check ZIP signature (docx is a zip file)
    if declared_mime in [
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]:
        # DOCX files are ZIP archives starting with PK
        return header.startswith(b'PK')
    
    if declared_mime == 'application/msword':
        # Old .doc format starts with D0 CF 11 E0
        return header.startswith(b'\xd0\xcf\x11\xe0')
    
    return detected_type == declared_mime


@router.post("")
async def upload_file(
    file: UploadFile = File(...), 
    user_id: str = Depends(get_current_user_id),
    org_id: int = Depends(get_current_org_id),
    workspace_id: Optional[int] = Depends(get_current_workspace_id),
):
    """
    Secure file upload endpoint.
    - Validates file size
    - Validates MIME type
    - Sanitizes filename via UUID generation
    - Stores in a dedicated non-executable directory
    """
    # 1. Validate declared MIME type is in allowed list
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed.",
        )

    # 1b. Validate file content matches declared MIME type
    if not _validate_file_content(file, file.content_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File content does not match declared type {file.content_type}. Possible spoofing attempt.",
        )

    # 2. Validate File Size
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE / 1024 / 1024}MB.",
        )

    # 3. Generate Secure Filename (UUID) with validated extension
    extension = Path(file.filename).suffix.lower()
    if not extension or len(extension) > 10:
        # Fallback to default extension based on content type
        extension = MIME_TYPE_EXTENSIONS.get(file.content_type, [".dat"])[0]
    elif extension not in MIME_TYPE_EXTENSIONS.get(file.content_type, []):
        # Extension doesn't match content type - use correct extension
        extension = MIME_TYPE_EXTENSIONS.get(file.content_type, [".dat"])[0]

    secure_filename = f"{uuid.uuid4()}{extension}"
    target_dir = UPLOAD_DIR / str(org_id)
    if workspace_id:
        target_dir = target_dir / str(workspace_id)
    else:
        target_dir = target_dir / "general"
        
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / secure_filename

    # 4. Save File securely
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file.",
        )

    return {
        "filename": secure_filename,
        "content_type": file.content_type,
        "size": file_size,
        "path": f"/api/v1/uploads/{org_id}/{workspace_id or 'general'}/{secure_filename}",
    }
