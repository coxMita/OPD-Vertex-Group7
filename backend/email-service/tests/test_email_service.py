"""Tests for EmailService."""

from unittest.mock import AsyncMock, patch

import pytest

from src.models.dto.email_event import EmailEvent
from src.services.email_service import EmailService


@pytest.fixture
def service() -> EmailService:
    """Return a fresh EmailService instance."""
    return EmailService()


@pytest.mark.asyncio
async def test_handle_event_without_document(service: EmailService) -> None:
    """Event with no document sends email with attachments=None."""
    event = EmailEvent(
        to_email="u@x.com",
        subject="Hi",
        message="Hello",
        is_html=True,
    )
    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send:
        await service.handle_event(event)

    mock_send.assert_called_once_with(
        to_email="u@x.com",
        subject="Hi",
        message="Hello",
        is_html=True,
        attachments=None,
    )


@pytest.mark.asyncio
async def test_handle_event_with_dict_document(service: EmailService) -> None:
    """Event with dict document_content generates a PDF attachment."""
    event = EmailEvent(
        to_email="u@x.com",
        subject="Prescription",
        message="See attached",
        is_html=True,
        document_title="My Report",
        document_content={"drug": "Aspirin", "dose": "500mg"},
    )
    with (
        patch(
            "src.services.email_service.send_email", new_callable=AsyncMock
        ) as mock_send,
        patch(
            "src.services.email_service.generate_pdf", return_value=b"FAKEPDF"
        ) as mock_pdf,
    ):
        await service.handle_event(event)

    mock_pdf.assert_called_once_with("My Report", {"drug": "Aspirin", "dose": "500mg"})
    mock_send.assert_called_once_with(
        to_email="u@x.com",
        subject="Prescription",
        message="See attached",
        is_html=True,
        attachments=[("My_Report.pdf", b"FAKEPDF")],
    )


@pytest.mark.asyncio
async def test_handle_event_with_str_document(service: EmailService) -> None:
    """Event with string document_content passes it directly to generate_pdf."""
    event = EmailEvent(
        to_email="u@x.com",
        subject="Notes",
        message="See attached",
        is_html=False,
        document_title="Notes",
        document_content="Patient notes here.",
    )
    with (
        patch("src.services.email_service.send_email", new_callable=AsyncMock),
        patch(
            "src.services.email_service.generate_pdf", return_value=b"PDF"
        ) as mock_pdf,
    ):
        await service.handle_event(event)

    mock_pdf.assert_called_once_with("Notes", "Patient notes here.")


@pytest.mark.asyncio
async def test_handle_event_title_only_no_attachment(service: EmailService) -> None:
    """document_title without document_content produces no PDF attachment."""
    event = EmailEvent(
        to_email="u@x.com",
        subject="Test",
        message="Body",
        is_html=False,
        document_title="Title Only",
    )
    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send:
        await service.handle_event(event)

    mock_send.assert_called_once_with(
        to_email="u@x.com",
        subject="Test",
        message="Body",
        is_html=False,
        attachments=None,
    )


@pytest.mark.asyncio
async def test_handle_event_content_only_no_attachment(
    service: EmailService,
) -> None:
    """document_content without document_title produces no PDF attachment."""
    event = EmailEvent(
        to_email="u@x.com",
        subject="Test",
        message="Body",
        is_html=False,
        document_content={"key": "value"},
    )
    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send:
        await service.handle_event(event)

    mock_send.assert_called_once_with(
        to_email="u@x.com",
        subject="Test",
        message="Body",
        is_html=False,
        attachments=None,
    )


@pytest.mark.asyncio
async def test_handle_event_filename_spaces_replaced(
    service: EmailService,
) -> None:
    """Spaces in document_title are replaced with underscores in the filename."""
    event = EmailEvent(
        to_email="u@x.com",
        subject="Report",
        message="See attached",
        is_html=True,
        document_title="My Patient Report",
        document_content="content",
    )
    with (
        patch(
            "src.services.email_service.send_email", new_callable=AsyncMock
        ) as mock_send,
        patch("src.services.email_service.generate_pdf", return_value=b"PDF"),
    ):
        await service.handle_event(event)

    _args, kwargs = mock_send.call_args
    assert kwargs["attachments"] == [("My_Patient_Report.pdf", b"PDF")]
