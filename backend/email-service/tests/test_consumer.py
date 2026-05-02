import contextlib
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

with contextlib.suppress(ImportError):
    pass

from src.messaging.email_queue_handler import process_message


@pytest.fixture
def mock_message() -> MagicMock:
    """Mock the aio_pika message."""
    mock_msg = MagicMock()
    mock_process_cm = AsyncMock()
    mock_process_cm.__aenter__.return_value = mock_msg
    mock_msg.process.return_value = mock_process_cm

    mock_msg.ack = AsyncMock()
    mock_msg.nack = AsyncMock()
    mock_msg.reject = AsyncMock()
    return mock_msg


@pytest.mark.asyncio
async def test_process_message_valid_event(mock_message: MagicMock) -> None:
    """Test successful processing of a valid email event message."""
    event_data = {
        "to_email": "user@example.com",
        "subject": "Welcome",
        "message": "Hello User!",
        "is_html": False,
    }
    mock_message.body = json.dumps(event_data).encode()

    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send_email:
        await process_message(mock_message)

        mock_send_email.assert_called_once_with(
            to_email="user@example.com",
            subject="Welcome",
            message="Hello User!",
            is_html=False,
            attachments=None,
        )
        mock_message.ack.assert_called_once()
        mock_message.nack.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_invalid_json(mock_message: MagicMock) -> None:
    """Test that invalid JSON messages are rejected."""
    mock_message.body = b"not valid json"

    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send_email:
        await process_message(mock_message)

        mock_send_email.assert_not_called()
        mock_message.reject.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_process_message_validation_error(mock_message: MagicMock) -> None:
    """Test that messages failing Pydantic validation are rejected."""
    mock_message.body = json.dumps({"subject": "test", "message": "msg"}).encode()

    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send_email:
        await process_message(mock_message)

        mock_send_email.assert_not_called()
        mock_message.reject.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_process_message_send_email_failure(mock_message: MagicMock) -> None:
    """Test message nacking and requeueing when sending email fails."""
    event_data = {
        "to_email": "user@example.com",
        "subject": "Welcome",
        "message": "Hello User!",
        "is_html": False,
    }
    mock_message.body = json.dumps(event_data).encode()

    with patch(
        "src.services.email_service.send_email", new_callable=AsyncMock
    ) as mock_send_email:
        mock_send_email.side_effect = Exception("SMTP error")

        await process_message(mock_message)

        mock_send_email.assert_called_once()
        mock_message.nack.assert_called_once_with(requeue=True)
        mock_message.ack.assert_not_called()


@pytest.mark.asyncio
async def test_process_message_with_document(mock_message: MagicMock) -> None:
    """Test successful processing of an email event with document data."""
    event_data = {
        "to_email": "user@example.com",
        "subject": "Prescription",
        "message": "See attached",
        "is_html": False,
        "document_title": "Rx",
        "document_content": {"medicine": "Paracetamol"},
    }
    mock_message.body = json.dumps(event_data).encode()

    with (
        patch(
            "src.services.email_service.send_email", new_callable=AsyncMock
        ) as mock_send_email,
        patch(
            "src.services.email_service.generate_pdf", return_value=b"mockpdf"
        ) as mock_generate_pdf,
    ):
        await process_message(mock_message)

        mock_generate_pdf.assert_called_once_with("Rx", {"medicine": "Paracetamol"})
        mock_send_email.assert_called_once_with(
            to_email="user@example.com",
            subject="Prescription",
            message="See attached",
            is_html=False,
            attachments=[("Rx.pdf", b"mockpdf")],
        )
        mock_message.ack.assert_called_once()
