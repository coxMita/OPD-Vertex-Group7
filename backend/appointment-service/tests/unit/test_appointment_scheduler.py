"""Unit tests for appointment scheduler helpers."""

import uuid
from datetime import date, time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.messaging.pubsub_exchanges import APPOINTMENT_SESSION_STARTED
from src.models.db.appointment import Appointment, AppointmentStatus, TimePreference
from src.scheduling.appointment_scheduler import _notify_session, build_scheduler

DOCTOR_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
OTHER_DOCTOR_ID = uuid.UUID("00000000-0000-0000-0001-000000000002")
PATIENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
EXPECTED_DOCTOR_MESSAGES = 2
EXPECTED_UPDATED_APPOINTMENTS = 3


def _make_appointment(
    doctor_id: uuid.UUID = DOCTOR_ID,
    assigned_time: time = time(8, 0),
) -> Appointment:
    """Create a test appointment entity."""
    appointment = Appointment(
        patient_id=PATIENT_ID,
        doctor_id=doctor_id,
        appointment_date=date.today(),
        time_preference=TimePreference.AM,
        assigned_time=assigned_time,
        notes="ready",
    )
    appointment.id = uuid.uuid4()
    return appointment


@pytest.mark.asyncio
async def test_notify_session_returns_when_no_appointments() -> None:
    """Session notification should skip publishing when there are no appointments."""
    repo = MagicMock()
    messaging = MagicMock()
    repo.get_by_date_and_preference.return_value = []

    await _notify_session(repo, messaging, TimePreference.AM)

    messaging.get_pubsub.assert_not_called()
    repo.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_notify_session_groups_by_doctor_and_marks_handed_off() -> None:
    """Session notification should publish one message per doctor and update status."""
    first = _make_appointment(DOCTOR_ID, time(8, 0))
    second = _make_appointment(DOCTOR_ID, time(9, 0))
    third = _make_appointment(OTHER_DOCTOR_ID, time(8, 0))
    repo = MagicMock()
    repo.get_by_date_and_preference.return_value = [first, second, third]
    pubsub = MagicMock()
    pubsub.publish = AsyncMock()
    messaging = MagicMock()
    messaging.get_pubsub.return_value = pubsub

    await _notify_session(repo, messaging, TimePreference.AM)

    messaging.get_pubsub.assert_called_once_with(APPOINTMENT_SESSION_STARTED)
    assert pubsub.publish.await_count == EXPECTED_DOCTOR_MESSAGES
    assert repo.update_status.call_count == EXPECTED_UPDATED_APPOINTMENTS
    repo.update_status.assert_any_call(first, AppointmentStatus.HANDED_OFF)
    repo.update_status.assert_any_call(second, AppointmentStatus.HANDED_OFF)
    repo.update_status.assert_any_call(third, AppointmentStatus.HANDED_OFF)


def test_build_scheduler_registers_am_and_pm_jobs() -> None:
    """Building the scheduler should register AM and PM notification jobs."""
    repo_factory = MagicMock()
    messaging = MagicMock()

    scheduler = build_scheduler(repo_factory, messaging)

    assert {job.id for job in scheduler.get_jobs()} == {
        "notify_am_session",
        "notify_pm_session",
    }
