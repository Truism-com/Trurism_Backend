"""
PDF Generation Service

Generates PDF documents for:
- Flight tickets
- Hotel vouchers
- Bus tickets
- Invoices
- Receipts
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from io import BytesIO

from app.core.config import settings

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF documents."""

    def __init__(self):
        self._weasyprint_available = False
        self._check_dependencies()

    def _check_dependencies(self):
        """Check if weasyprint is available."""
        try:
            import weasyprint
            self._weasyprint_available = True
        except ImportError:
            logger.warning(
                "weasyprint not installed. PDF generation will use fallback. "
                "Install with: pip install weasyprint"
            )

    def _get_base_styles(self) -> str:
        """Get base CSS styles for PDF documents."""
        return """
        @page {
            size: A4;
            margin: 1cm;
        }
        body {
            font-family: Arial, Helvetica, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
        }
        .header {
            background: #1e40af;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .header p {
            margin: 5px 0 0 0;
            font-size: 14px;
            opacity: 0.9;
        }
        .section {
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
        }
        .section-title {
            font-size: 14px;
            font-weight: bold;
            color: #1e40af;
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid #1e40af;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table td, table th {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }
        table th {
            background: #f3f4f6;
            font-weight: bold;
        }
        .highlight {
            background: #fef3c7;
            padding: 10px;
            border-left: 4px solid #f59e0b;
        }
        .footer {
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #e5e7eb;
            font-size: 10px;
            color: #666;
            text-align: center;
        }
        .amount {
            font-size: 18px;
            font-weight: bold;
            color: #059669;
        }
        .barcode {
            text-align: center;
            margin: 20px 0;
            font-family: monospace;
            font-size: 14px;
            letter-spacing: 2px;
        }
        """

    def _generate_html_to_pdf(self, html_content: str) -> bytes:
        """Convert HTML to PDF using weasyprint."""
        if self._weasyprint_available:
            import weasyprint
            pdf = weasyprint.HTML(string=html_content).write_pdf()
            return pdf
        else:
            return html_content.encode("utf-8")

    def generate_flight_ticket(
        self,
        booking_reference: str,
        pnr: str,
        passenger_name: str,
        flight_number: str,
        airline: str,
        origin: str,
        destination: str,
        departure_time: str,
        arrival_time: str,
        travel_class: str,
        seat_number: Optional[str] = None,
        baggage: Optional[str] = None,
        tenant_name: Optional[str] = None,
        tenant_logo: Optional[str] = None,
    ) -> bytes:
        """Generate flight ticket PDF."""
        tenant = tenant_name or settings.app_name

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>{self._get_base_styles()}</style>
        </head>
        <body>
            <div class="header">
                <h1>{tenant}</h1>
                <p>E-Ticket / Itinerary</p>
            </div>

            <div class="section">
                <div class="section-title">Booking Details</div>
                <table>
                    <tr>
                        <td><strong>Booking Reference:</strong></td>
                        <td>{booking_reference}</td>
                        <td><strong>PNR:</strong></td>
                        <td style="font-size: 16px; font-weight: bold;">{pnr}</td>
                    </tr>
                    <tr>
                        <td><strong>Passenger Name:</strong></td>
                        <td colspan="3">{passenger_name}</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">Flight Details</div>
                <table>
                    <tr>
                        <th>Flight</th>
                        <th>From</th>
                        <th>To</th>
                        <th>Class</th>
                    </tr>
                    <tr>
                        <td>{airline} {flight_number}</td>
                        <td>{origin}<br><small>{departure_time}</small></td>
                        <td>{destination}<br><small>{arrival_time}</small></td>
                        <td>{travel_class}</td>
                    </tr>
                </table>
            </div>

            {"<div class='section'><div class='section-title'>Additional Information</div><table>" +
             f"<tr><td><strong>Seat:</strong></td><td>{seat_number}</td></tr>" if seat_number else "" +
             f"<tr><td><strong>Baggage:</strong></td><td>{baggage}</td></tr>" if baggage else "" +
             "</table></div>" if seat_number or baggage else ""}

            <div class="highlight">
                <strong>Important:</strong> Please arrive at the airport at least 2 hours 
                before departure for domestic flights and 3 hours for international flights.
            </div>

            <div class="barcode">
                {booking_reference}
            </div>

            <div class="footer">
                <p>This is a computer-generated document. No signature required.</p>
                <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>{tenant} | Contact Support for assistance</p>
            </div>
        </body>
        </html>
        """
        return self._generate_html_to_pdf(html)

    def generate_hotel_voucher(
        self,
        booking_reference: str,
        guest_name: str,
        hotel_name: str,
        hotel_address: str,
        check_in: str,
        check_out: str,
        room_type: str,
        rooms: int,
        guests: int,
        meal_plan: Optional[str] = None,
        special_requests: Optional[str] = None,
        confirmation_number: Optional[str] = None,
        tenant_name: Optional[str] = None,
    ) -> bytes:
        """Generate hotel voucher PDF."""
        tenant = tenant_name or settings.app_name

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>{self._get_base_styles()}</style>
        </head>
        <body>
            <div class="header">
                <h1>{tenant}</h1>
                <p>Hotel Voucher</p>
            </div>

            <div class="section">
                <div class="section-title">Booking Information</div>
                <table>
                    <tr>
                        <td><strong>Voucher No:</strong></td>
                        <td>{booking_reference}</td>
                        <td><strong>Confirmation No:</strong></td>
                        <td>{confirmation_number or 'Pending'}</td>
                    </tr>
                    <tr>
                        <td><strong>Guest Name:</strong></td>
                        <td colspan="3">{guest_name}</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">Hotel Details</div>
                <table>
                    <tr>
                        <td><strong>Hotel:</strong></td>
                        <td colspan="3">{hotel_name}</td>
                    </tr>
                    <tr>
                        <td><strong>Address:</strong></td>
                        <td colspan="3">{hotel_address}</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">Stay Details</div>
                <table>
                    <tr>
                        <th>Check-In</th>
                        <th>Check-Out</th>
                        <th>Room Type</th>
                        <th>Rooms/Guests</th>
                    </tr>
                    <tr>
                        <td>{check_in}</td>
                        <td>{check_out}</td>
                        <td>{room_type}</td>
                        <td>{rooms} Room(s) / {guests} Guest(s)</td>
                    </tr>
                </table>
                {f"<p><strong>Meal Plan:</strong> {meal_plan}</p>" if meal_plan else ""}
                {f"<p><strong>Special Requests:</strong> {special_requests}</p>" if special_requests else ""}
            </div>

            <div class="highlight">
                <strong>Note:</strong> Please present this voucher at the hotel reception 
                during check-in along with a valid photo ID.
            </div>

            <div class="footer">
                <p>This voucher is valid only for the dates mentioned above.</p>
                <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p>{tenant}</p>
            </div>
        </body>
        </html>
        """
        return self._generate_html_to_pdf(html)

    def generate_invoice(
        self,
        invoice_number: str,
        customer_name: str,
        customer_email: str,
        customer_address: Optional[str],
        items: list[Dict[str, Any]],
        subtotal: float,
        taxes: float,
        total: float,
        payment_status: str,
        payment_method: Optional[str] = None,
        transaction_id: Optional[str] = None,
        invoice_date: Optional[str] = None,
        due_date: Optional[str] = None,
        tenant_name: Optional[str] = None,
        tenant_address: Optional[str] = None,
        tenant_gst: Optional[str] = None,
    ) -> bytes:
        """Generate invoice PDF."""
        tenant = tenant_name or settings.app_name
        inv_date = invoice_date or datetime.now().strftime("%Y-%m-%d")

        items_html = ""
        for idx, item in enumerate(items, 1):
            items_html += f"""
            <tr>
                <td>{idx}</td>
                <td>{item.get('description', '')}</td>
                <td>{item.get('quantity', 1)}</td>
                <td style="text-align: right;">INR {item.get('rate', 0):,.2f}</td>
                <td style="text-align: right;">INR {item.get('amount', 0):,.2f}</td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                {self._get_base_styles()}
                .invoice-header {{
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 30px;
                }}
                .company-info {{ text-align: left; }}
                .invoice-info {{ text-align: right; }}
                .totals {{ margin-top: 20px; }}
                .totals td {{ padding: 5px 10px; }}
                .grand-total {{ font-size: 16px; font-weight: bold; background: #f3f4f6; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>TAX INVOICE</h1>
            </div>

            <table style="margin-bottom: 30px;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <strong>{tenant}</strong><br>
                        {tenant_address or ''}<br>
                        {f"GST: {tenant_gst}" if tenant_gst else ''}
                    </td>
                    <td style="width: 50%; text-align: right; vertical-align: top;">
                        <strong>Invoice No:</strong> {invoice_number}<br>
                        <strong>Date:</strong> {inv_date}<br>
                        {f"<strong>Due Date:</strong> {due_date}<br>" if due_date else ''}
                    </td>
                </tr>
            </table>

            <div class="section">
                <div class="section-title">Bill To</div>
                <p>
                    <strong>{customer_name}</strong><br>
                    {customer_email}<br>
                    {customer_address or ''}
                </p>
            </div>

            <div class="section">
                <div class="section-title">Invoice Items</div>
                <table>
                    <tr>
                        <th>#</th>
                        <th>Description</th>
                        <th>Qty</th>
                        <th style="text-align: right;">Rate</th>
                        <th style="text-align: right;">Amount</th>
                    </tr>
                    {items_html}
                </table>

                <table class="totals" style="width: 300px; margin-left: auto;">
                    <tr>
                        <td>Subtotal:</td>
                        <td style="text-align: right;">INR {subtotal:,.2f}</td>
                    </tr>
                    <tr>
                        <td>Taxes (GST):</td>
                        <td style="text-align: right;">INR {taxes:,.2f}</td>
                    </tr>
                    <tr class="grand-total">
                        <td>Total:</td>
                        <td style="text-align: right;">INR {total:,.2f}</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <div class="section-title">Payment Information</div>
                <table>
                    <tr>
                        <td><strong>Status:</strong></td>
                        <td>{payment_status}</td>
                    </tr>
                    {f"<tr><td><strong>Method:</strong></td><td>{payment_method}</td></tr>" if payment_method else ''}
                    {f"<tr><td><strong>Transaction ID:</strong></td><td>{transaction_id}</td></tr>" if transaction_id else ''}
                </table>
            </div>

            <div class="footer">
                <p>Thank you for your business!</p>
                <p>This is a computer-generated invoice.</p>
                <p>{tenant}</p>
            </div>
        </body>
        </html>
        """
        return self._generate_html_to_pdf(html)

    def generate_receipt(
        self,
        receipt_number: str,
        customer_name: str,
        amount: float,
        payment_method: str,
        transaction_id: str,
        description: str,
        receipt_date: Optional[str] = None,
        tenant_name: Optional[str] = None,
    ) -> bytes:
        """Generate payment receipt PDF."""
        tenant = tenant_name or settings.app_name
        date = receipt_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>{self._get_base_styles()}</style>
        </head>
        <body>
            <div class="header">
                <h1>{tenant}</h1>
                <p>Payment Receipt</p>
            </div>

            <div class="section">
                <table>
                    <tr>
                        <td><strong>Receipt No:</strong></td>
                        <td>{receipt_number}</td>
                    </tr>
                    <tr>
                        <td><strong>Date:</strong></td>
                        <td>{date}</td>
                    </tr>
                    <tr>
                        <td><strong>Received From:</strong></td>
                        <td>{customer_name}</td>
                    </tr>
                </table>
            </div>

            <div class="section" style="text-align: center;">
                <p>Amount Received</p>
                <p class="amount">INR {amount:,.2f}</p>
                <p><em>{description}</em></p>
            </div>

            <div class="section">
                <div class="section-title">Payment Details</div>
                <table>
                    <tr>
                        <td><strong>Payment Method:</strong></td>
                        <td>{payment_method}</td>
                    </tr>
                    <tr>
                        <td><strong>Transaction ID:</strong></td>
                        <td>{transaction_id}</td>
                    </tr>
                </table>
            </div>

            <div class="footer">
                <p>This is a computer-generated receipt. No signature required.</p>
                <p>{tenant}</p>
            </div>
        </body>
        </html>
        """
        return self._generate_html_to_pdf(html)


pdf_service = PDFService()
