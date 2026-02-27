"""File management API endpoints."""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query, Path
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import os

from app.auth.api import get_current_user
from app.auth.models import User
from app.services import StorageService, PDFService
from .schemas import (
    FileType,
    FileUploadResponse,
    FileInfoResponse,
    FileDeleteResponse,
    FileListResponse,
    PDFGenerateRequest,
    PDFGenerateResponse,
)

router = APIRouter(prefix="/files", tags=["Files"])

# Initialize services
storage_service = StorageService()
pdf_service = PDFService()


# =============================================================================
# KYC Document Uploads
# =============================================================================

@router.post("/kyc/{user_id}", response_model=FileUploadResponse)
async def upload_kyc_document(
    user_id: str = Path(..., description="User ID"),
    doc_type: str = Query(..., description="Document type: passport, aadhaar, pan, etc."),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload KYC document for a user.
    
    Requires admin role or document owner.
    """
    # Check permissions
    if not current_user.is_admin and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to upload for this user")
    
    try:
        file_path = await storage_service.save_kyc_document(
            file=file,
            user_id=user_id,
            document_type=doc_type,
        )
        
        # Get file size
        file_info = await storage_service.get_file_info(file_path)
        
        return FileUploadResponse(
            success=True,
            file_path=file_path,
            filename=file.filename or "unknown",
            file_type=FileType.KYC,
            size=file_info.get("size", 0),
            message=f"KYC document '{doc_type}' uploaded successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# =============================================================================
# Profile Picture Uploads
# =============================================================================

@router.post("/profile/{user_id}", response_model=FileUploadResponse)
async def upload_profile_picture(
    user_id: str = Path(..., description="User ID"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload profile picture for a user.
    
    Requires admin role or profile owner.
    """
    # Check permissions
    if not current_user.is_admin and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to upload for this user")
    
    try:
        file_path = await storage_service.save_profile_picture(
            file=file,
            user_id=user_id,
        )
        
        file_info = await storage_service.get_file_info(file_path)
        
        return FileUploadResponse(
            success=True,
            file_path=file_path,
            filename=file.filename or "unknown",
            file_type=FileType.PROFILE,
            size=file_info.get("size", 0),
            message="Profile picture uploaded successfully",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# =============================================================================
# General Document Uploads
# =============================================================================

@router.post("/documents/{user_id}", response_model=FileUploadResponse)
async def upload_document(
    user_id: str = Path(..., description="User ID"),
    category: str = Query("general", description="Document category"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a general document for a user.
    """
    if not current_user.is_admin and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        file_path = await storage_service.save_file(
            file=file,
            directory=f"documents/{user_id}/{category}",
            allowed_types=["application/pdf", "image/jpeg", "image/png"],
        )
        
        file_info = await storage_service.get_file_info(file_path)
        
        return FileUploadResponse(
            success=True,
            file_path=file_path,
            filename=file.filename or "unknown",
            file_type=FileType.DOCUMENT,
            size=file_info.get("size", 0),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# File Downloads
# =============================================================================

@router.get("/download/{file_type}/{user_id}/{filename}")
async def download_file(
    file_type: FileType,
    user_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """
    Download a file.
    
    Requires admin role or file owner.
    """
    if not current_user.is_admin and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Build file path based on type
    if file_type == FileType.KYC:
        file_path = f"kyc/{user_id}/{filename}"
    elif file_type == FileType.PROFILE:
        file_path = f"profiles/{user_id}/{filename}"
    elif file_type == FileType.TICKET:
        file_path = f"tickets/{user_id}/{filename}"
    elif file_type == FileType.INVOICE:
        file_path = f"invoices/{user_id}/{filename}"
    else:
        file_path = f"documents/{user_id}/{filename}"
    
    try:
        content = await storage_service.get_file(file_path)
        if content is None:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine content type
        if filename.endswith(".pdf"):
            media_type = "application/pdf"
        elif filename.endswith((".jpg", ".jpeg")):
            media_type = "image/jpeg"
        elif filename.endswith(".png"):
            media_type = "image/png"
        else:
            media_type = "application/octet-stream"
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


# =============================================================================
# PDF Generation
# =============================================================================

@router.post("/pdf/flight-ticket/{booking_id}", response_model=PDFGenerateResponse)
async def generate_flight_ticket(
    booking_id: str = Path(..., description="Booking ID"),
    current_user: User = Depends(get_current_user),
):
    """
    Generate PDF flight ticket for a booking.
    """
    # TODO: Fetch actual booking data from database
    # For now, use sample data
    booking_data = {
        "pnr": "ABC123",
        "passenger_name": "John Doe",
        "flight_number": "AI 101",
        "departure_city": "Mumbai",
        "arrival_city": "Delhi",
        "departure_time": "10:00",
        "arrival_time": "12:00",
        "departure_date": "2024-01-15",
        "seat_number": "12A",
        "class": "Economy",
        "airline": "Air India",
    }
    
    try:
        pdf_bytes = await pdf_service.generate_flight_ticket(booking_data)
        
        filename = f"ticket_{booking_id}.pdf"
        user_id = str(current_user.id)
        
        # Save to storage
        file_path = await storage_service.save_ticket(
            file_content=pdf_bytes,
            user_id=user_id,
            booking_id=booking_id,
        )
        
        return PDFGenerateResponse(
            success=True,
            file_path=file_path,
            filename=filename,
            message="Flight ticket PDF generated successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/pdf/hotel-voucher/{booking_id}", response_model=PDFGenerateResponse)
async def generate_hotel_voucher(
    booking_id: str = Path(..., description="Booking ID"),
    current_user: User = Depends(get_current_user),
):
    """
    Generate PDF hotel voucher for a booking.
    """
    # TODO: Fetch actual booking data
    booking_data = {
        "voucher_number": f"HV-{booking_id}",
        "guest_name": "John Doe",
        "hotel_name": "Grand Hotel",
        "hotel_address": "123 Main St, Mumbai",
        "check_in_date": "2024-01-15",
        "check_out_date": "2024-01-17",
        "room_type": "Deluxe",
        "meal_plan": "Breakfast Included",
        "guests": 2,
    }
    
    try:
        pdf_bytes = await pdf_service.generate_hotel_voucher(booking_data)
        
        filename = f"voucher_{booking_id}.pdf"
        user_id = str(current_user.id)
        
        file_path = await storage_service.save_ticket(
            file_content=pdf_bytes,
            user_id=user_id,
            booking_id=booking_id,
        )
        
        return PDFGenerateResponse(
            success=True,
            file_path=file_path,
            filename=filename,
            message="Hotel voucher PDF generated successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.post("/pdf/invoice/{booking_id}", response_model=PDFGenerateResponse)
async def generate_invoice(
    booking_id: str = Path(..., description="Booking ID"),
    current_user: User = Depends(get_current_user),
):
    """
    Generate PDF invoice for a booking.
    """
    # TODO: Fetch actual invoice data
    invoice_data = {
        "invoice_number": f"INV-{booking_id}",
        "invoice_date": "2024-01-10",
        "due_date": "2024-01-20",
        "customer_name": "John Doe",
        "customer_email": "john@example.com",
        "customer_address": "123 Main St, Mumbai",
        "items": [
            {"description": "Flight Ticket - AI 101", "quantity": 1, "unit_price": 5000, "total": 5000},
            {"description": "Service Fee", "quantity": 1, "unit_price": 200, "total": 200},
        ],
        "subtotal": 5200,
        "tax": 936,
        "total": 6136,
        "company_name": "Travel Agency",
        "company_address": "456 Business St, Mumbai",
        "company_email": "info@agency.com",
    }
    
    try:
        pdf_bytes = await pdf_service.generate_invoice(invoice_data)
        
        filename = f"invoice_{booking_id}.pdf"
        user_id = str(current_user.id)
        
        file_path = await storage_service.save_invoice(
            file_content=pdf_bytes,
            user_id=user_id,
            invoice_id=booking_id,
        )
        
        return PDFGenerateResponse(
            success=True,
            file_path=file_path,
            filename=filename,
            message="Invoice PDF generated successfully",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


# =============================================================================
# File Management
# =============================================================================

@router.delete("/{file_type}/{user_id}/{filename}", response_model=FileDeleteResponse)
async def delete_file(
    file_type: FileType,
    user_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """
    Delete a file.
    
    Requires admin role.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Build file path
    if file_type == FileType.KYC:
        file_path = f"kyc/{user_id}/{filename}"
    elif file_type == FileType.PROFILE:
        file_path = f"profiles/{user_id}/{filename}"
    else:
        file_path = f"documents/{user_id}/{filename}"
    
    try:
        success = await storage_service.delete_file(file_path)
        return FileDeleteResponse(
            success=success,
            message="File deleted successfully" if success else "File not found",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/info/{file_type}/{user_id}/{filename}", response_model=FileInfoResponse)
async def get_file_info(
    file_type: FileType,
    user_id: str,
    filename: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get file information.
    """
    if not current_user.is_admin and str(current_user.id) != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if file_type == FileType.KYC:
        file_path = f"kyc/{user_id}/{filename}"
    elif file_type == FileType.PROFILE:
        file_path = f"profiles/{user_id}/{filename}"
    else:
        file_path = f"documents/{user_id}/{filename}"
    
    try:
        info = await storage_service.get_file_info(file_path)
        if not info:
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileInfoResponse(**info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
