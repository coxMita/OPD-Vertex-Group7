"""Tests for the email queue message handler."""

import json
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from src.messaging.email_queue_handler import process_message


@pytest.fixture
def mock_message() -> MagicMock:
    """Return a mock aio_pika message with async process() context manager."""
    msg = MagicMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = msg
    msg.process.return_value = cm
    msg.ack = AsyncMock()
    msg.nack = AsyncMock()
    msg.reject = AsyncMock()
    return msg


@pytest.mark.asyncio
async def test_process_message_valid_html_event(mock_message: MagicMock) -> None:
    """Valid HTML email event is sent and message is acknowledged."""
    event_data = {
        "to_email": "user@example.com",
        "subject": "Welcome",
        "message": "<p>Hello User!</p>",
        "is_html": True,
    }
    mock_message.body = json.dumps(event_data).encode()

    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send:
        await process_message(mock_message)

        mock_send.assert_called_once_with(
            to_email="user@example.com",
            subject="Welcome",
            message="<p>Hello User!</p>",
            is_html=True,
            attachments=None,
        )
        mock_message.ack.assert_called_once()
        mock_message.nack.assert_not_called()


@pytest.mark.asyncio
async def test_plain_text_is_wrapped_in_html_template(
    mock_message: MagicMock,
) -> None:
    """Plain-text events are rendered through generic.html before sending."""
    event_data = {
        "to_email": "user@example.com",
        "subject": "Welcome",
        "message": "Hello User!",
        "is_html": False,
    }
    mock_message.body = json.dumps(event_data).encode()

    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send:
        await process_message(mock_message)

        mock_send.assert_called_once_with(
            to_email="user@example.com",
            subject="Welcome",
            message=ANY,  # template-rendered HTML
            is_html=True,
            attachments=None,
        )
        mock_message.ack.assert_called_once()


@pytest.mark.asyncio
async def test_process_message_invalid_json(mock_message: MagicMock) -> None:
    """Invalid JSON body is rejected without requeuing."""
    mock_message.body = b"not valid json"

    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send:
        await process_message(mock_message)

        mock_send.assert_not_called()
        mock_message.reject.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_process_message_validation_error(mock_message: MagicMock) -> None:
    """Messages failing Pydantic validation are rejected without requeuing."""
    mock_message.body = json.dumps({"subject": "test", "message": "msg"}).encode()

    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send:
        await process_message(mock_message)

        mock_send.assert_not_called()
        mock_message.reject.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_process_message_send_failure_requeues(
    mock_message: MagicMock,
) -> None:
    """SMTP failure causes the message to be nacked with requeue=True."""
    event_data = {
        "to_email": "user@example.com",
        "subject": "Welcome",
        "message": "<p>Hello!</p>",
        "is_html": True,
    }
    mock_message.body = json.dumps(event_data).encode()

    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send:
        mock_send.side_effect = Exception("SMTP error")

        await process_message(mock_message)

        mock_message.nack.assert_called_once_with(requeue=True)
        mock_message.ack.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_with_document(mock_message: MagicMock) -> None:
    """Events with document data generate a PDF attachment then ack."""
    event_data = {
        "to_email": "user@example.com",
        "subject": "Prescription",
        "message": "See attached",
        "is_html": True,
        "document_title": "Rx",
        "document_content": {"medicine": "Paracetamol"},
    }
    mock_message.body = json.dumps(event_data).encode()

    with (
        patch(
            "src.services.email_service.send_email", new_callable=AsyncMock
        ) as mock_send,
        patch(
            "src.services.email_service.generate_pdf", return_value=b"mockpdf"
        ) as mock_pdf,
    ):
        await process_message(mock_message)

        mock_pdf.assert_called_once_with("Rx", {"medicine": "Paracetamol"})
        mock_send.assert_called_once_with(
            to_email="user@example.com",
            subject="Prescription",
            message="See attached",
            is_html=True,
            attachments=[("Rx.pdf", b"mockpdf")],
        )
        mock_message.ack.assert_called_once()
