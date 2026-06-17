"""
Booking Celery Tasks

Background tasks for flight ticket issuance via AIR IQ.

Task: issue_flight_ticket
- Called after payment is captured and booking record is created
- Posts to AIR IQ /book endpoint to issue the real ticket
- Updates booking status: CONFIRMED (success) or TICKETING_FAILED (failure)
- On failure: triggers wallet refund if payment was wallet-based
- Sends confirmation or failure email

Worker command:
    celery -A app.celery.celery_app worker --loglevel=info

"""

import logging
from typing import Any, Dict, List

from app.celery import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    name="booking.issue_flight_ticket",
)
def issue_flight_ticket(
    self,
    booking_id: int,
    ticket_id: str,
    adult_info: List[Dict[str, Any]],
    child_info: List[Dict[str, Any]],
    infant_info: List[Dict[str, Any]],
    user_id: int,
    user_email: str,
    user_name: str,
    booking_reference: str,
    payment_method: str,
    total_amount: float,
) -> Dict[str, Any]:
    """
    Issue flight ticket via AIR IQ POST /book.

    Called after payment captured. Updates booking to CONFIRMED or TICKETING_FAILED.
    On TICKETING_FAILED with wallet payment: triggers refund.

    Args:
        booking_id: FlightBooking.id in our DB
        ticket_id: AIR IQ ticket_id from search (e.g. "12907125_2596")
        adult_info: List of adult passenger dicts per AIR IQ spec
        child_info: List of child passenger dicts per AIR IQ spec
        infant_info: List of infant passenger dicts per AIR IQ spec
        user_id: User ID for refund processing
        user_email: For email notification
        user_name: For email notification
        booking_reference: Our internal reference (e.g. "BK20260615ABCD1234")
        payment_method: "wallet" or other - used to determine if refund needed
        total_amount: Amount to refund on failure

    WARNING: This task issues a real ticket via AIR IQ and charges the AIR IQ wallet.
    Do not re-enqueue for the same booking_id if it already has status=CONFIRMED.
    """
    import asyncio
    return asyncio.run(_issue_flight_ticket_async(
        self,
        booking_id=booking_id,
        ticket_id=ticket_id,
        adult_info=adult_info,
        child_info=child_info,
        infant_info=infant_info,
        user_id=user_id,
        user_email=user_email,
        user_name=user_name,
        booking_reference=booking_reference,
        payment_method=payment_method,
        total_amount=total_amount,
    ))


async def _issue_flight_ticket_async(
    task,
    booking_id: int,
    ticket_id: str,
    adult_info: List[Dict[str, Any]],
    child_info: List[Dict[str, Any]],
    infant_info: List[Dict[str, Any]],
    user_id: int,
    user_email: str,
    user_name: str,
    booking_reference: str,
    payment_method: str,
    total_amount: float,
) -> Dict[str, Any]:
    """
    Async implementation of ticket issuance.
    Separated so Celery sync task can call asyncio.run() cleanly.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.core.config import settings
    from app.booking.models import FlightBooking, BookingStatus, PaymentStatus
    from app.search.airiq_client import AirIQClient
    from sqlalchemy import select

    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        try:
            # Guard: check booking not already confirmed
            result = await db.execute(
                select(FlightBooking).where(FlightBooking.id == booking_id)
            )
            booking = result.scalar_one_or_none()

            if not booking:
                logger.error("issue_flight_ticket: booking_id=%s not found", booking_id)
                return {"success": False, "error": "Booking not found"}

            if booking.status == BookingStatus.CONFIRMED:
                logger.warning(
                    "issue_flight_ticket: booking_id=%s already CONFIRMED, skipping", booking_id
                )
                return {"success": True, "skipped": True}

            # Call AIR IQ
            airiq = AirIQClient()
            try:
                airiq_result = await airiq.book_ticket(
                    ticket_id=ticket_id,
                    adult_info=adult_info,
                    child_info=child_info,
                    infant_info=infant_info,
                )
            finally:
                await airiq.close()

            if airiq_result.get("success"):
                airiq_booking_id = airiq_result.get("booking_id", "")

                # Fetch PNR from ticket details
                pnr = ""
                try:
                    airiq_detail = AirIQClient()
                    try:
                        details = await airiq_detail.get_ticket_details(airiq_booking_id)
                        pnr = details.get("pnr", "")
                    finally:
                        await airiq_detail.close()
                except Exception as pnr_err:
                    logger.warning("Could not fetch PNR: %s", pnr_err)

                booking.status = BookingStatus.CONFIRMED
                booking.payment_status = PaymentStatus.SUCCESS
                booking.airiq_booking_id = airiq_booking_id
                booking.confirmation_number = airiq_booking_id
                booking.pnr = pnr or airiq_booking_id
                await db.commit()

                logger.info(
                    "Ticket issued. booking_id=%s airiq_booking_id=%s pnr=%s",
                    booking_id, airiq_booking_id, pnr
                )

                # Send confirmation email (non-blocking failure)
                try:
                    from app.services.email import email_service
                    await email_service.send_booking_confirmation(
                        to_email=user_email,
                        booking_reference=booking_reference,
                        service_type="Flight",
                        travel_date=str(booking.departure_time.date()),
                        amount=float(booking.total_amount),
                        passenger_name=user_name,
                    )
                except Exception as email_err:
                    logger.warning("Confirmation email failed: %s", email_err)

                return {"success": True, "airiq_booking_id": airiq_booking_id, "pnr": pnr}

            else:
                # Ticket issuance failed
                error = airiq_result.get("error", "AIR IQ booking failed")
                logger.error(
                    "Ticket issuance failed. booking_id=%s error=%s", booking_id, error
                )

                booking.status = BookingStatus.TICKETING_FAILED
                await db.commit()

                # Refund wallet if payment was wallet
                if payment_method == "wallet":
                    try:
                        from app.booking.payment_processor import BookingPaymentProcessor, PaymentMode
                        from decimal import Decimal
                        processor = BookingPaymentProcessor(db)
                        await processor.process_refund(
                            user_id=user_id,
                            amount=Decimal(str(total_amount)),
                            booking_id=booking_id,
                            booking_type="flight",
                            original_payment_method=payment_method,
                            reason=f"Ticket issuance failed: {error}",
                        )
                        booking.payment_status = PaymentStatus.REFUNDED
                        await db.commit()
                    except Exception as refund_err:
                        logger.error(
                            "Refund failed for booking_id=%s: %s", booking_id, refund_err
                        )

                # Send failure email
                try:
                    from app.services.email import email_service
                    await email_service.send_booking_confirmation(
                        to_email=user_email,
                        booking_reference=booking_reference,
                        service_type="Flight - FAILED",
                        travel_date="",
                        amount=float(total_amount),
                        passenger_name=user_name,
                    )
                except Exception as email_err:
                    logger.warning("Failure email failed: %s", email_err)

                return {"success": False, "error": error}

        except Exception as exc:
            await db.rollback()
            logger.error(
                "issue_flight_ticket task exception. booking_id=%s: %s",
                booking_id, exc, exc_info=True
            )
            # Retry up to max_retries
            raise task.retry(exc=exc)
        finally:
            await engine.dispose()
