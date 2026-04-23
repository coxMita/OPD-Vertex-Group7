from unittest.mock import AsyncMock, patch

import pytest

from src.services.smtp_delivery import send_email


@pytest.mark.asyncio
async def test_send_email_plain_text() -> None:
    """Test sending plain text emails using mocked aiosmtplib.send."""
    with patch(
        "src.services.smtp_delivery.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await send_email(
            to_email="test@example.com",
            subject="Test Subject",
            message="Test Message",
            is_html=False,
        )
        mock_send.assert_called_once()

        args, _kwargs = mock_send.call_args
        email_msg = args[0]
        assert email_msg["To"] == "test@example.com"
        assert email_msg["Subject"] == "Test Subject"
        assert email_msg.get_content().strip() == "Test Message"


@pytest.mark.asyncio
async def test_send_email_html() -> None:
    """Test sending HTML emails using mocked aiosmtplib.send."""
    with patch(
        "src.services.smtp_delivery.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await send_email(
            to_email="test@example.com",
            subject="Test HTML Subject",
            message="<p>HTML Content</p>",
            is_html=True,
        )
        mock_send.assert_called_once()

        args, _kwargs = mock_send.call_args
        email_msg = args[0]
        assert email_msg["To"] == "test@example.com"
        assert email_msg["Subject"] == "Test HTML Subject"
