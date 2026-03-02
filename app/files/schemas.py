"""Pydantic schemas for file operations."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    """Allowed file types."""
    KYC = "kyc"
    PROFILE = "profile"
    DOCUMENT = "document"
    TICKET = "ticket"
    INVOICE = "invoice"


class FileUploadResponse(BaseModel):
    """Response after file upload."""
    success: bool
    file_path: str
    filename: str
    file_type: FileType
    size: int
    message: str = "File uploaded successfully"


class FileInfoResponse(BaseModel):
    """File information response."""
    filename: str
    size: int
    content_type: Optional[str] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None


class FileDeleteResponse(BaseModel):
    """Response after file deletion."""
    success: bool
    message: str


class FileListResponse(BaseModel):
    """List of files response."""
    files: list[str]
    total: int


class PDFGenerateRequest(BaseModel):
    """Request to generate PDF."""
    booking_id: str
    pdf_type: str = Field(..., description="Type: flight_ticket, hotel_voucher, invoice, receipt")


class PDFGenerateResponse(BaseModel):
    """Response after PDF generation."""
    success: bool
    file_path: str
    filename: str
    message: str = "PDF generated successfully"
