"""Tests for SMTP email delivery."""

from email.message import EmailMessage
from unittest.mock import AsyncMock, patch

import pytest

from src.config import settings
from src.services.smtp_delivery import SMTP_SSL_PORT, send_email


@pytest.mark.asyncio
async def test_send_plain_text_sets_headers_and_body() -> None:
    """Plain-text email has correct To, Subject, and body content."""
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
        email_msg: EmailMessage = mock_send.call_args.args[0]
        assert email_msg["To"] == "test@example.com"
        assert email_msg["Subject"] == "Test Subject"
        assert email_msg.get_content().strip() == "Test Message"


@pytest.mark.asyncio
async def test_send_html_email_sets_headers() -> None:
    """HTML email has correct To and Subject headers."""
    with patch(
        "src.services.smtp_delivery.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await send_email(
            to_email="test@example.com",
            subject="HTML Subject",
            message="<p>HTML Content</p>",
            is_html=True,
        )
        mock_send.assert_called_once()
        email_msg: EmailMessage = mock_send.call_args.args[0]
        assert email_msg["To"] == "test@example.com"
        assert email_msg["Subject"] == "HTML Subject"


@pytest.mark.asyncio
async def test_send_email_with_pdf_attachment() -> None:
    """Email with an attachment includes the file in the MIME parts."""
    with patch(
        "src.services.smtp_delivery.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await send_email(
            to_email="test@example.com",
            subject="With Attachment",
            message="See attached",
            is_html=False,
            attachments=[("report.pdf", b"%PDF-1.4")],
        )
        mock_send.assert_called_once()
        email_msg: EmailMessage = mock_send.call_args.args[0]
        filenames = [part.get_filename() for part in email_msg.iter_attachments()]
        assert "report.pdf" in filenames


@pytest.mark.asyncio
async def test_ssl_port_enables_use_tls(monkeypatch: pytest.MonkeyPatch) -> None:
    """Port 465 with SMTP_USE_TLS=True sets use_tls=True and start_tls=False."""
    monkeypatch.setattr(settings, "SMTP_PORT", SMTP_SSL_PORT)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

    with patch(
        "src.services.smtp_delivery.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await send_email(to_email="t@x.com", subject="S", message="m")
        _args, kwargs = mock_send.call_args
        assert kwargs["use_tls"] is True
        assert kwargs["start_tls"] is False


@pytest.mark.asyncio
async def test_starttls_port_enables_start_tls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Port 587 with SMTP_USE_TLS=True sets start_tls=True and use_tls=False."""
    _starttls_port = 587
    monkeypatch.setattr(settings, "SMTP_PORT", _starttls_port)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

    with patch(
        "src.services.smtp_delivery.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await send_email(to_email="t@x.com", subject="S", message="m")
        _args, kwargs = mock_send.call_args
        assert kwargs["use_tls"] is False
        assert kwargs["start_tls"] is True


@pytest.mark.asyncio
async def test_credentials_forwarded_to_smtp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Configured SMTP credentials are included in the aiosmtplib call."""
    monkeypatch.setattr(settings, "SMTP_USER", "user@example.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "secret")

    with patch(
        "src.services.smtp_delivery.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await send_email(to_email="t@x.com", subject="S", message="m")
        _args, kwargs = mock_send.call_args
        assert kwargs["username"] == "user@example.com"
        assert kwargs["password"] == "secret"  # noqa: S105


@pytest.mark.asyncio
async def test_no_credentials_omits_auth_kwargs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty SMTP credentials do not add username/password to the call."""
    monkeypatch.setattr(settings, "SMTP_USER", "")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")

    with patch(
        "src.services.smtp_delivery.aiosmtplib.send", new_callable=AsyncMock
    ) as mock_send:
        await send_email(to_email="t@x.com", subject="S", message="m")
        _args, kwargs = mock_send.call_args
        assert "username" not in kwargs
        assert "password" not in kwargs


@pytest.mark.asyncio
async def test_smtp_error_is_re_raised() -> None:
    """Aiosmtplib exceptions are logged and propagated to the caller."""
    with (
        patch(
            "src.services.smtp_delivery.aiosmtplib.send",
            new_callable=AsyncMock,
            side_effect=ConnectionError("refused"),
        ),
        pytest.raises(ConnectionError, match="refused"),
    ):
        await send_email(
            to_email="test@example.com",
            subject="Fail",
            message="msg",
        )
