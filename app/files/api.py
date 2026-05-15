"""File management API endpoints."""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Query, Path
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import os
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.api import get_current_user
from app.auth.models import User
from app.core.database import get_database_session
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
    
    # Sanitize filename to prevent path traversal
    if ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    filename = os.path.basename(filename)
    
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
    db: AsyncSession = Depends(get_database_session),
):
    """
    Generate PDF flight ticket for a booking.
    """
    from app.booking.services import FlightBookingService
    booking_service = FlightBookingService(db)
    booking = await booking_service.get_flight_booking(int(booking_id), current_user.id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking_data = {
        "pnr": booking.pnr or "",
        "passenger_name": current_user.name,
        "flight_number": booking.flight_number,
        "departure_city": booking.origin,
        "arrival_city": booking.destination,
        "departure_time": booking.departure_time.strftime("%H:%M") if booking.departure_time else "",
        "arrival_time": booking.arrival_time.strftime("%H:%M") if booking.arrival_time else "",
        "departure_date": booking.departure_time.strftime("%Y-%m-%d") if booking.departure_time else "",
        "seat_number": "",
        "class": booking.travel_class or "Economy",
        "airline": booking.airline,
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
    db: AsyncSession = Depends(get_database_session),
):
    """
    Generate PDF hotel voucher for a booking.
    """
    from app.booking.services import HotelBookingService
    booking_service = HotelBookingService(db)
    booking = await booking_service.get_hotel_booking(int(booking_id), current_user.id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking_data = {
        "voucher_number": f"HV-{booking_id}",
        "guest_name": current_user.name,
        "hotel_name": booking.hotel_name,
        "hotel_address": booking.hotel_address or "",
        "check_in_date": booking.checkin_date.strftime("%Y-%m-%d") if booking.checkin_date else "",
        "check_out_date": booking.checkout_date.strftime("%Y-%m-%d") if booking.checkout_date else "",
        "room_type": "Standard",
        "meal_plan": "",
        "guests": booking.adults + booking.children,
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
    db: AsyncSession = Depends(get_database_session),
):
    """
    Generate PDF invoice for a booking.
    """
    from app.booking.services import FlightBookingService, HotelBookingService, BusBookingService

    booking = None
    booking_type = "booking"

    flight_svc = FlightBookingService(db)
    booking = await flight_svc.get_flight_booking(int(booking_id), current_user.id)
    if booking:
        booking_type = "flight"
        description = f"Flight Ticket - {booking.airline} {booking.flight_number}"
        base_amount = booking.base_fare
        tax_amount = booking.taxes
        total = booking.total_amount
    else:
        hotel_svc = HotelBookingService(db)
        booking = await hotel_svc.get_hotel_booking(int(booking_id), current_user.id)
        if booking:
            booking_type = "hotel"
            description = f"Hotel Stay - {booking.hotel_name}"
            base_amount = getattr(booking, 'base_amount', booking.room_rate * booking.nights * booking.rooms)
            tax_amount = getattr(booking, 'taxes', 0.0)
            total = booking.total_amount
        else:
            bus_svc = BusBookingService(db)
            booking = await bus_svc.get_bus_booking(int(booking_id), current_user.id)
            if booking:
                booking_type = "bus"
                description = f"Bus Ticket - {booking.operator}"
                base_amount = getattr(booking, 'base_amount', booking.fare_per_passenger * booking.passengers)
                tax_amount = getattr(booking, 'taxes', 0.0)
                total = booking.total_amount

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    invoice_data = {
        "invoice_number": f"INV-{booking_id}",
        "invoice_date": booking.created_at.strftime("%Y-%m-%d") if booking.created_at else "",
        "due_date": "",
        "customer_name": current_user.name,
        "customer_email": current_user.email,
        "customer_address": current_user.address or "",
        "items": [
            {"description": description, "quantity": 1, "unit_price": base_amount, "total": base_amount},
        ],
        "subtotal": base_amount,
        "tax": tax_amount,
        "total": total,
        "company_name": "Trurism",
        "company_address": "",
        "company_email": "",
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
    
    # Sanitize filename to prevent path traversal
    if ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    filename = os.path.basename(filename)
    
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
    
    # Sanitize filename to prevent path traversal
    if ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    filename = os.path.basename(filename)
    
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
