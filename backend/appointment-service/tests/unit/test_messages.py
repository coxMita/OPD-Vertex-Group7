"""Unit tests for appointment message models."""

import uuid
from datetime import date, time

from src.models.db.appointment import TimePreference
from src.models.msg.session_started_message import (
    AppointmentSlot,
    SessionStartedMessage,
)

DOCTOR_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
PATIENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_session_started_message_serializes_round_trip() -> None:
    """SessionStartedMessage should serialize and deserialize through bytes."""
    message = SessionStartedMessage(
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        time_preference=TimePreference.AM,
        appointments=[
            AppointmentSlot(
                appointment_id=uuid.uuid4(),
                patient_id=PATIENT_ID,
                assigned_time=time(8, 0),
                notes="first",
            )
        ],
    )

    parsed = SessionStartedMessage.from_bytes(message.to_bytes())

    assert parsed == message
    assert str(message).startswith("SessionStartedMessage(")
