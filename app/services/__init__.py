"""
Core Services Module

Provides cross-cutting services used across the application:
- Email notifications
- SMS messaging
- PDF generation
- File storage
- Export utilities
"""

import logging as _logging

# aiosmtplib is an optional dependency. If it is missing from the deployed
# virtualenv (e.g. stale Azure Oryx build cache), the app must still boot.
# Callers that use EmailService must check for None before instantiating.
try:
    from app.services.email import EmailService, EmailTemplate
except ImportError as _e:
    _logging.getLogger(__name__).warning(
        "Email service is unavailable (missing dependency: %s). "
        "Email sending will be disabled until the package is installed.",
        _e,
    )
    EmailService = None  # type: ignore[assignment,misc]
    EmailTemplate = None  # type: ignore[assignment,misc]

from app.services.pdf import PDFService
from app.services.storage import StorageService

__all__ = [
    "EmailService",
    "EmailTemplate",
    "PDFService",
    "StorageService",
]
