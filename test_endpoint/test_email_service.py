import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_email_not_sent_when_unconfigured():

    from app.services.email import EmailService

    service = EmailService()

    with patch.object(type(service), "is_configured", new_callable=lambda: property(lambda s: False)):
        try:
            await service.send_welcome(to_email="x@x.com", user_name="X")
        except Exception as e:
            pytest.fail(f"Unconfigured email service raised: {e}")


@pytest.mark.asyncio
async def test_smtp_error_is_caught_and_logged():

    from app.services.email import EmailService
    import aiosmtplib

    service = EmailService()
    with patch("aiosmtplib.send", side_effect=aiosmtplib.SMTPException("conn refused")):
        with patch.object(type(service), "is_configured",new_callable=lambda: property(lambda s: True)):
            try:
                await service.send_welcome(to_email="x@x.com", user_name="X")
            except Exception as e:
                pytest.fail(f"SMTP error leaked out of service: {e}")