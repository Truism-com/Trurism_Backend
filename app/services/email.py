"""
Email Service

Handles all email notifications for the platform:
- Booking confirmations
- Password reset
- OTP verification
- Agent approval notifications
- Payment receipts
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATE_DIR = Path(__file__).parent / "templates" / "email"


class EmailTemplate:
    """Email template identifiers."""
    BOOKING_CONFIRMATION = "booking_confirmation"
    BOOKING_CANCELLATION = "booking_cancellation"
    PASSWORD_RESET = "password_reset"
    OTP_VERIFICATION = "otp_verification"
    WELCOME = "welcome"
    AGENT_APPROVAL = "agent_approval"
    AGENT_REJECTION = "agent_rejection"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    REFUND_PROCESSED = "refund_processed"
    ENQUIRY_RECEIVED = "enquiry_received"
    CREDIT_REQUEST = "credit_request"
    WALLET_TOPUP = "wallet_topup"


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        self.smtp_host = settings.mail_server
        self.smtp_port = settings.mail_port
        self.smtp_user = settings.mail_from
        self.smtp_password = settings.mail_password
        self.from_email = settings.mail_from
        self.from_name = settings.app_name
        self._template_env = None

    @property
    def is_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(
            self.smtp_host
            and self.smtp_port
            and self.smtp_user
            and self.smtp_password
        )

    def _get_template_env(self) -> Environment:
        """Get or create Jinja2 template environment."""
        if self._template_env is None:
            if TEMPLATE_DIR.exists():
                self._template_env = Environment(
                    loader=FileSystemLoader(str(TEMPLATE_DIR)),
                    autoescape=select_autoescape(["html", "xml"]),
                )
            else:
                self._template_env = Environment(autoescape=True)
        return self._template_env

    def _render_template(
        self, template_name: str, context: Dict[str, Any]
    ) -> tuple[str, str]:
        """Render email template to HTML and plain text."""
        env = self._get_template_env()

        context["app_name"] = settings.app_name
        context["support_email"] = self.from_email

        try:
            html_template = env.get_template(f"{template_name}.html")
            html_content = html_template.render(**context)
        except Exception:
            html_content = self._get_default_html(template_name, context)

        try:
            text_template = env.get_template(f"{template_name}.txt")
            text_content = text_template.render(**context)
        except Exception:
            text_content = self._get_default_text(template_name, context)

        return html_content, text_content

    def _get_default_html(
        self, template_name: str, context: Dict[str, Any]
    ) -> str:
        """Generate default HTML email content."""
        subject = context.get("subject", "Notification")
        body = context.get("body", "")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #2563eb; 
                          color: white; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{settings.app_name}</h1>
                </div>
                <div class="content">
                    <h2>{subject}</h2>
                    <p>{body}</p>
                    {self._get_template_specific_content(template_name, context)}
                </div>
                <div class="footer">
                    <p>This is an automated message from {settings.app_name}.</p>
                    <p>Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _get_template_specific_content(
        self, template_name: str, context: Dict[str, Any]
    ) -> str:
        """Get template-specific HTML content."""
        if template_name == EmailTemplate.BOOKING_CONFIRMATION:
            return f"""
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td><strong>Booking Reference:</strong></td>
                    <td>{context.get('booking_reference', 'N/A')}</td></tr>
                <tr><td><strong>Service:</strong></td>
                    <td>{context.get('service_type', 'N/A')}</td></tr>
                <tr><td><strong>Date:</strong></td>
                    <td>{context.get('travel_date', 'N/A')}</td></tr>
                <tr><td><strong>Amount:</strong></td>
                    <td>INR {context.get('amount', '0.00')}</td></tr>
            </table>
            """
        elif template_name == EmailTemplate.PASSWORD_RESET:
            reset_link = context.get("reset_link", "#")
            return f"""
            <p>Click the button below to reset your password:</p>
            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Reset Password</a>
            </p>
            <p style="font-size: 12px; color: #666;">
                This link will expire in 1 hour.
            </p>
            """
        elif template_name == EmailTemplate.OTP_VERIFICATION:
            otp = context.get("otp", "000000")
            return f"""
            <p style="text-align: center; font-size: 32px; letter-spacing: 8px; 
                      font-weight: bold; background: #e5e7eb; padding: 20px;">
                {otp}
            </p>
            <p style="font-size: 12px; color: #666;">
                This OTP is valid for 10 minutes.
            </p>
            """
        elif template_name == EmailTemplate.PAYMENT_SUCCESS:
            return f"""
            <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                <tr><td><strong>Transaction ID:</strong></td>
                    <td>{context.get('transaction_id', 'N/A')}</td></tr>
                <tr><td><strong>Amount Paid:</strong></td>
                    <td>INR {context.get('amount', '0.00')}</td></tr>
                <tr><td><strong>Payment Method:</strong></td>
                    <td>{context.get('payment_method', 'N/A')}</td></tr>
            </table>
            """
        return ""

    def _get_default_text(
        self, template_name: str, context: Dict[str, Any]
    ) -> str:
        """Generate default plain text email content."""
        subject = context.get("subject", "Notification")
        body = context.get("body", "")
        return f"{subject}\n\n{body}\n\n--\n{settings.app_name}"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        template: str,
        context: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[tuple[str, bytes, str]]] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an email using the configured SMTP server.

        Args:
            to_email: Recipient email address
            subject: Email subject
            template: Template name from EmailTemplate
            context: Template context variables
            attachments: List of (filename, content, mimetype) tuples
            cc: CC recipients
            bcc: BCC recipients

        Returns:
            bool: True if email sent successfully
        """
        if not self.is_configured:
            logger.warning("Email service not configured, skipping send")
            return False

        context = context or {}
        context["subject"] = subject

        try:
            html_content, text_content = self._render_template(template, context)

            message = MIMEMultipart("alternative")
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            message["Subject"] = subject

            if cc:
                message["Cc"] = ", ".join(cc)

            message.attach(MIMEText(text_content, "plain", "utf-8"))
            message.attach(MIMEText(html_content, "html", "utf-8"))

            if attachments:
                for filename, content, mimetype in attachments:
                    main_type, sub_type = mimetype.split("/", 1)
                    part = MIMEBase(main_type, sub_type)
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={filename}",
                    )
                    message.attach(part)

            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_booking_confirmation(
        self,
        to_email: str,
        booking_reference: str,
        service_type: str,
        travel_date: str,
        amount: float,
        passenger_name: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send booking confirmation email."""
        context = {
            "booking_reference": booking_reference,
            "service_type": service_type,
            "travel_date": travel_date,
            "amount": f"{amount:,.2f}",
            "passenger_name": passenger_name,
            "body": f"Dear {passenger_name}, your booking has been confirmed.",
            **(details or {}),
        }
        return await self.send_email(
            to_email=to_email,
            subject=f"Booking Confirmed - {booking_reference}",
            template=EmailTemplate.BOOKING_CONFIRMATION,
            context=context,
        )

    async def send_password_reset(
        self, to_email: str, reset_link: str, user_name: str
    ) -> bool:
        """Send password reset email."""
        context = {
            "reset_link": reset_link,
            "user_name": user_name,
            "body": f"Dear {user_name}, we received a request to reset your password.",
        }
        return await self.send_email(
            to_email=to_email,
            subject="Password Reset Request",
            template=EmailTemplate.PASSWORD_RESET,
            context=context,
        )

    async def send_otp(self, to_email: str, otp: str, purpose: str = "verification") -> bool:
        """Send OTP verification email."""
        context = {
            "otp": otp,
            "purpose": purpose,
            "body": f"Your OTP for {purpose} is:",
        }
        return await self.send_email(
            to_email=to_email,
            subject=f"OTP for {purpose.title()}",
            template=EmailTemplate.OTP_VERIFICATION,
            context=context,
        )

    async def send_payment_success(
        self,
        to_email: str,
        transaction_id: str,
        amount: float,
        payment_method: str,
        booking_reference: Optional[str] = None,
    ) -> bool:
        """Send payment success notification."""
        context = {
            "transaction_id": transaction_id,
            "amount": f"{amount:,.2f}",
            "payment_method": payment_method,
            "booking_reference": booking_reference,
            "body": "Your payment has been processed successfully.",
        }
        return await self.send_email(
            to_email=to_email,
            subject=f"Payment Successful - {transaction_id}",
            template=EmailTemplate.PAYMENT_SUCCESS,
            context=context,
        )

    async def send_welcome(self, to_email: str, user_name: str) -> bool:
        """Send welcome email to new users."""
        context = {
            "user_name": user_name,
            "body": f"Welcome to {settings.app_name}! Your account has been created successfully.",
        }
        return await self.send_email(
            to_email=to_email,
            subject=f"Welcome to {settings.app_name}",
            template=EmailTemplate.WELCOME,
            context=context,
        )

    async def send_agent_approval(
        self, to_email: str, agent_name: str, company_name: str
    ) -> bool:
        """Send agent approval notification."""
        context = {
            "agent_name": agent_name,
            "company_name": company_name,
            "body": f"Congratulations! Your agent account for {company_name} has been approved.",
        }
        return await self.send_email(
            to_email=to_email,
            subject="Agent Account Approved",
            template=EmailTemplate.AGENT_APPROVAL,
            context=context,
        )


email_service = EmailService()
