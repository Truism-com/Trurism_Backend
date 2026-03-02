"""
File Storage Service

Handles file uploads and storage for:
- KYC documents
- Profile pictures
- Ticket PDFs
- Invoices
"""

import logging
import os
import uuid
import hashlib
from typing import Optional, BinaryIO, Tuple
from pathlib import Path
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


class StorageService:
    """Service for file storage operations."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else UPLOAD_DIR
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary upload directories."""
        directories = [
            self.base_path,
            self.base_path / "kyc",
            self.base_path / "profiles",
            self.base_path / "documents",
            self.base_path / "tickets",
            self.base_path / "invoices",
            self.base_path / "temp",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _generate_filename(
        self, original_filename: str, prefix: Optional[str] = None
    ) -> str:
        """Generate unique filename preserving extension."""
        ext = Path(original_filename).suffix.lower()
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime("%Y%m%d")
        
        if prefix:
            return f"{prefix}_{timestamp}_{unique_id}{ext}"
        return f"{timestamp}_{unique_id}{ext}"

    def _validate_file(
        self, filename: str, content: bytes, allowed_types: Optional[set] = None
    ) -> Tuple[bool, str]:
        """Validate file type and size."""
        ext = Path(filename).suffix.lower()
        allowed = allowed_types or ALLOWED_EXTENSIONS

        if ext not in allowed:
            return False, f"File type {ext} not allowed. Allowed: {', '.join(allowed)}"

        if len(content) > MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed ({MAX_FILE_SIZE // (1024*1024)}MB)"

        return True, ""

    def _compute_hash(self, content: bytes) -> str:
        """Compute SHA256 hash of file content."""
        return hashlib.sha256(content).hexdigest()

    async def save_file(
        self,
        content: bytes,
        filename: str,
        folder: str = "documents",
        prefix: Optional[str] = None,
        allowed_types: Optional[set] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Save file to storage.

        Args:
            content: File content as bytes
            filename: Original filename
            folder: Subfolder to save in (kyc, profiles, documents, etc.)
            prefix: Optional prefix for generated filename
            allowed_types: Optional set of allowed extensions

        Returns:
            Tuple of (success, message/error, file_path if success)
        """
        try:
            is_valid, error = self._validate_file(filename, content, allowed_types)
            if not is_valid:
                return False, error, None

            new_filename = self._generate_filename(filename, prefix)
            folder_path = self.base_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)

            file_path = folder_path / new_filename
            file_path.write_bytes(content)

            relative_path = f"{folder}/{new_filename}"
            logger.info(f"File saved: {relative_path}")

            return True, "File saved successfully", relative_path

        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            return False, str(e), None

    async def save_kyc_document(
        self,
        content: bytes,
        filename: str,
        user_id: int,
        document_type: str,
    ) -> Tuple[bool, str, Optional[str]]:
        """Save KYC document for a user."""
        prefix = f"kyc_{user_id}_{document_type}"
        return await self.save_file(
            content=content,
            filename=filename,
            folder="kyc",
            prefix=prefix,
            allowed_types={".jpg", ".jpeg", ".png", ".pdf"},
        )

    async def save_profile_picture(
        self, content: bytes, filename: str, user_id: int
    ) -> Tuple[bool, str, Optional[str]]:
        """Save profile picture for a user."""
        prefix = f"profile_{user_id}"
        return await self.save_file(
            content=content,
            filename=filename,
            folder="profiles",
            prefix=prefix,
            allowed_types={".jpg", ".jpeg", ".png"},
        )

    async def save_ticket(
        self, content: bytes, booking_reference: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Save generated ticket PDF."""
        filename = f"{booking_reference}.pdf"
        return await self.save_file(
            content=content,
            filename=filename,
            folder="tickets",
            prefix=booking_reference,
            allowed_types={".pdf"},
        )

    async def save_invoice(
        self, content: bytes, invoice_number: str
    ) -> Tuple[bool, str, Optional[str]]:
        """Save generated invoice PDF."""
        filename = f"{invoice_number}.pdf"
        return await self.save_file(
            content=content,
            filename=filename,
            folder="invoices",
            prefix=invoice_number,
            allowed_types={".pdf"},
        )

    async def get_file(self, file_path: str) -> Optional[bytes]:
        """Retrieve file content."""
        try:
            full_path = self.base_path / file_path
            if full_path.exists() and full_path.is_file():
                return full_path.read_bytes()
            return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            full_path = self.base_path / file_path
            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False

    async def get_file_info(self, file_path: str) -> Optional[dict]:
        """Get file metadata."""
        try:
            full_path = self.base_path / file_path
            if not full_path.exists():
                return None

            stat = full_path.stat()
            return {
                "path": file_path,
                "filename": full_path.name,
                "size": stat.st_size,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": full_path.suffix,
            }
        except Exception as e:
            logger.error(f"Failed to get file info {file_path}: {e}")
            return None

    def get_file_url(self, file_path: str) -> str:
        """Get URL for accessing a file."""
        return f"/api/v1/files/{file_path}"


storage_service = StorageService()
