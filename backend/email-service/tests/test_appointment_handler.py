"""Tests for the appointment pub/sub event handler."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.messaging.appointment_handler import (
    FALLBACK_EMAIL,
    _fetch_patient,
    process_appointment_message,
)

_PATIENT_ID = str(uuid.uuid4())
_DOCTOR_ID = str(uuid.uuid4())
_APPOINTMENT_ID = str(uuid.uuid4())

_SCHEDULED_BODY = {
    "appointment_id": _APPOINTMENT_ID,
    "patient_id": _PATIENT_ID,
    "doctor_id": _DOCTOR_ID,
    "appointment_date": "2026-06-01",
    "time_preference": "AM",
    "assigned_time": "09:00:00",
    "status": "scheduled",
}


def _make_msg(
    status: str = "scheduled",
    exchange: str = "appointment.created",
    assigned_time: str | None = "09:00:00",
) -> MagicMock:
    """Build a mock aio_pika message for the given appointment status."""
    msg = MagicMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = msg
    msg.process.return_value = cm
    msg.ack = AsyncMock()
    msg.nack = AsyncMock()
    msg.reject = AsyncMock()
    msg.exchange = exchange
    msg.body = json.dumps(
        {
            "appointment_id": _APPOINTMENT_ID,
            "patient_id": _PATIENT_ID,
            "doctor_id": _DOCTOR_ID,
            "appointment_date": "2026-06-01",
            "time_preference": "AM",
            "assigned_time": assigned_time,
            "status": status,
        }
    ).encode()
    return msg


def _patch_http_client(
    mock_client: AsyncMock,
) -> patch:  # type: ignore[type-arg]
    """Return a context-manager patch for httpx.AsyncClient in appointment_handler."""
    p = patch("src.messaging.appointment_handler.httpx.AsyncClient")
    return p


# ── _fetch_patient ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_patient_returns_data_on_200() -> None:
    """_fetch_patient returns the parsed JSON from a successful user-service call."""
    patient = {"first_name": "Alice", "last_name": "Smith", "email": "a@x.com"}
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = patient

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch(
        "src.messaging.appointment_handler.httpx.AsyncClient"
    ) as mock_http_client:
        mock_http_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_http_client.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await _fetch_patient(_PATIENT_ID)

    assert result["email"] == "a@x.com"
    assert result["first_name"] == "Alice"


@pytest.mark.asyncio
async def test_fetch_patient_non_200_returns_fallback() -> None:
    """Non-200 user-service response falls back to the team inbox."""
    mock_response = MagicMock()
    mock_response.status_code = 404

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    with patch(
        "src.messaging.appointment_handler.httpx.AsyncClient"
    ) as mock_http_client:
        mock_http_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_http_client.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await _fetch_patient(_PATIENT_ID)

    assert result["email"] == FALLBACK_EMAIL


@pytest.mark.asyncio
async def test_fetch_patient_http_error_returns_fallback() -> None:
    """Network error from user-service returns the fallback patient record."""
    mock_client = AsyncMock()
    mock_client.get.side_effect = httpx.HTTPError("timeout")

    with patch(
        "src.messaging.appointment_handler.httpx.AsyncClient"
    ) as mock_http_client:
        mock_http_client.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_http_client.return_value.__aexit__ = AsyncMock(return_value=False)
        result = await _fetch_patient(_PATIENT_ID)

    assert result["email"] == FALLBACK_EMAIL
    assert result["first_name"] == "Patient"


# ── process_appointment_message ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scheduled_via_created_exchange_sends_booking_email() -> None:
    """SCHEDULED from 'appointment.created' triggers a booking confirmation."""
    msg = _make_msg(status="scheduled", exchange="appointment.created")

    with (
        patch(
            "src.messaging.appointment_handler._fetch_patient",
            new_callable=AsyncMock,
            return_value={"email": "p@x.com", "first_name": "Bob"},
        ),
        patch(
            "src.messaging.appointment_handler._email_service.handle_event",
            new_callable=AsyncMock,
        ) as mock_handle,
    ):
        await process_appointment_message(msg)

    mock_handle.assert_called_once()
    email_event = mock_handle.call_args.args[0]
    assert email_event.to_email == "p@x.com"
    assert "Confirmation" in email_event.subject
    assert email_event.is_html is True
    msg.ack.assert_called_once()
    msg.nack.assert_not_called()


@pytest.mark.asyncio
async def test_scheduled_via_status_exchange_sends_reschedule_email() -> None:
    """SCHEDULED from 'appointment.status_changed' triggers a reschedule email."""
    msg = _make_msg(status="scheduled", exchange="appointment.status_changed")

    with (
        patch(
            "src.messaging.appointment_handler._fetch_patient",
            new_callable=AsyncMock,
            return_value={"email": "p@x.com", "first_name": "Carol"},
        ),
        patch(
            "src.messaging.appointment_handler._email_service.handle_event",
            new_callable=AsyncMock,
        ) as mock_handle,
    ):
        await process_appointment_message(msg)

    email_event = mock_handle.call_args.args[0]
    assert "Rescheduled" in email_event.subject
    msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_cancelled_sends_cancellation_email() -> None:
    """CANCELLED status triggers a cancellation email."""
    msg = _make_msg(status="cancelled")

    with (
        patch(
            "src.messaging.appointment_handler._fetch_patient",
            new_callable=AsyncMock,
            return_value={"email": "p@x.com", "first_name": "Dave"},
        ),
        patch(
            "src.messaging.appointment_handler._email_service.handle_event",
            new_callable=AsyncMock,
        ) as mock_handle,
    ):
        await process_appointment_message(msg)

    email_event = mock_handle.call_args.args[0]
    assert "Cancelled" in email_event.subject
    msg.ack.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["handed_off", "completed"])
async def test_ignored_status_acks_without_email(status: str) -> None:
    """Non-actionable statuses are acknowledged without sending any email."""
    msg = _make_msg(status=status)

    with patch(
        "src.messaging.appointment_handler._email_service.handle_event",
        new_callable=AsyncMock,
    ) as mock_handle:
        await process_appointment_message(msg)

    mock_handle.assert_not_called()
    msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_invalid_json_is_rejected() -> None:
    """Invalid JSON body is rejected without requeuing."""
    msg = MagicMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = msg
    msg.process.return_value = cm
    msg.ack = AsyncMock()
    msg.nack = AsyncMock()
    msg.reject = AsyncMock()
    msg.body = b"not json"

    await process_appointment_message(msg)
    msg.reject.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_validation_error_is_rejected() -> None:
    """Malformed appointment payload is rejected without requeuing."""
    msg = MagicMock()
    cm = AsyncMock()
    cm.__aenter__.return_value = msg
    msg.process.return_value = cm
    msg.ack = AsyncMock()
    msg.nack = AsyncMock()
    msg.reject = AsyncMock()
    msg.body = json.dumps({"status": "scheduled"}).encode()

    await process_appointment_message(msg)
    msg.reject.assert_called_once_with(requeue=False)


@pytest.mark.asyncio
async def test_email_send_failure_nacks_with_requeue() -> None:
    """Email service error causes nack(requeue=True) on the message."""
    msg = _make_msg(status="scheduled")

    with (
        patch(
            "src.messaging.appointment_handler._fetch_patient",
            new_callable=AsyncMock,
            return_value={"email": "p@x.com", "first_name": "Eve"},
        ),
        patch(
            "src.messaging.appointment_handler._email_service.handle_event",
            new_callable=AsyncMock,
            side_effect=Exception("SMTP error"),
        ),
    ):
        await process_appointment_message(msg)

    msg.nack.assert_called_once_with(requeue=True)
    msg.ack.assert_not_called()


@pytest.mark.asyncio
async def test_no_assigned_time_uses_time_preference() -> None:
    """Appointment with assigned_time=None uses time_preference in the template."""
    msg = _make_msg(
        status="scheduled",
        exchange="appointment.created",
        assigned_time=None,
    )

    with (
        patch(
            "src.messaging.appointment_handler._fetch_patient",
            new_callable=AsyncMock,
            return_value={"email": "p@x.com", "first_name": "Frank"},
        ),
        patch(
            "src.messaging.appointment_handler._email_service.handle_event",
            new_callable=AsyncMock,
        ) as mock_handle,
    ):
        await process_appointment_message(msg)

    mock_handle.assert_called_once()
    msg.ack.assert_called_once()


@pytest.mark.asyncio
async def test_fallback_email_used_when_patient_email_missing() -> None:
    """Missing email in patient data falls back to the team inbox address."""
    msg = _make_msg(status="scheduled", exchange="appointment.created")

    with (
        patch(
            "src.messaging.appointment_handler._fetch_patient",
            new_callable=AsyncMock,
            return_value={"first_name": "Ghost"},  # no 'email' key
        ),
        patch(
            "src.messaging.appointment_handler._email_service.handle_event",
            new_callable=AsyncMock,
        ) as mock_handle,
    ):
        await process_appointment_message(msg)

    email_event = mock_handle.call_args.args[0]
    assert email_event.to_email == FALLBACK_EMAIL
