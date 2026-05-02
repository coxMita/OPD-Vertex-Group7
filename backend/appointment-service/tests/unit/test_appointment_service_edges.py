"""Additional unit tests for AppointmentService edge cases."""

import asyncio
import uuid
from datetime import date, time
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.messaging.pubsub_exchanges import (
    APPOINTMENT_CREATED,
    APPOINTMENT_STATUS_CHANGED,
)
from src.models.db.appointment import Appointment, AppointmentStatus, TimePreference
from src.models.dto.appointment_create_request import AppointmentCreateRequest
from src.models.dto.appointment_reschedule_request import AppointmentRescheduleRequest
from src.services.appointment_service import AppointmentService

DOCTOR_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
OTHER_PATIENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
PATIENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _make_appointment(
    appointment_id: uuid.UUID | None = None,
    patient_id: uuid.UUID = PATIENT_ID,
    time_preference: TimePreference = TimePreference.AM,
    assigned_time: time = time(8, 0),
    status: AppointmentStatus = AppointmentStatus.SCHEDULED,
) -> Appointment:
    """Create a test appointment entity."""
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        time_preference=time_preference,
        assigned_time=assigned_time,
        status=status,
        notes="bring notes",
    )
    appointment.id = appointment_id or uuid.uuid4()
    return appointment


@pytest.fixture
def repo() -> MagicMock:
    """Return a mocked appointment repository."""
    return MagicMock()


@pytest.fixture
def pubsub() -> MagicMock:
    """Return a mocked pubsub facade."""
    facade = MagicMock()
    facade.publish = AsyncMock()
    return facade


@pytest.fixture
def messaging(pubsub: MagicMock) -> MagicMock:
    """Return a mocked messaging manager."""
    manager = MagicMock()
    manager.get_pubsub.return_value = pubsub
    return manager


@pytest.fixture
def service(repo: MagicMock, messaging: MagicMock) -> AppointmentService:
    """Return an appointment service with mocked dependencies."""
    return AppointmentService(repo, messaging)


@pytest.mark.asyncio
async def test_create_appointment_publishes_created_event(
    service: AppointmentService,
    repo: MagicMock,
    messaging: MagicMock,
    pubsub: MagicMock,
) -> None:
    """Creating an appointment should publish a created event."""
    appointment = _make_appointment()
    repo.get_by_doctor_date_and_preference.return_value = []
    repo.create.return_value = appointment

    result = service.create_appointment(
        AppointmentCreateRequest(
            patient_id=PATIENT_ID,
            doctor_id=DOCTOR_ID,
            appointment_date=date(2026, 3, 10),
            time_preference=TimePreference.AM,
        )
    )
    await asyncio.sleep(0)

    assert result.id == appointment.id
    messaging.get_pubsub.assert_called_once_with(APPOINTMENT_CREATED)
    pubsub.publish.assert_awaited_once()


def test_get_appointment_returns_response(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Getting an existing appointment should return a response DTO."""
    appointment = _make_appointment()
    repo.get_by_id.return_value = appointment

    result = service.get_appointment(appointment.id)

    assert result is not None
    assert result.id == appointment.id


def test_get_appointment_returns_none(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Getting a missing appointment should return None."""
    repo.get_by_id.return_value = None

    assert service.get_appointment(uuid.uuid4()) is None


def test_get_queue_returns_ordered_responses(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Getting a queue should map repository appointments to DTOs."""
    first = _make_appointment(assigned_time=time(8, 0))
    second = _make_appointment(assigned_time=time(9, 0))
    repo.get_by_doctor_and_date.return_value = [first, second]

    result = service.get_queue(DOCTOR_ID, date(2026, 3, 10))

    assert [appointment.assigned_time for appointment in result] == [
        time(8, 0),
        time(9, 0),
    ]


def test_get_patient_appointments_returns_responses(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Getting patient appointments should map entities to response DTOs."""
    appointment = _make_appointment()
    repo.get_by_patient_id.return_value = [appointment]

    result = service.get_patient_appointments(PATIENT_ID)

    assert len(result) == 1
    assert result[0].patient_id == PATIENT_ID


def test_cancel_by_patient_returns_none_when_missing(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Cancelling a missing appointment should return None."""
    repo.get_by_id.return_value = None

    assert service.cancel_by_patient(uuid.uuid4(), PATIENT_ID) is None


def test_cancel_by_patient_rejects_other_patient(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Cancelling another patient's appointment should be forbidden."""
    repo.get_by_id.return_value = _make_appointment(patient_id=OTHER_PATIENT_ID)

    assert service.cancel_by_patient(uuid.uuid4(), PATIENT_ID) == "forbidden"


def test_cancel_by_patient_rejects_non_scheduled(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Cancelling a non-scheduled appointment should return conflict."""
    repo.get_by_id.return_value = _make_appointment(status=AppointmentStatus.COMPLETED)

    assert service.cancel_by_patient(uuid.uuid4(), PATIENT_ID) == "conflict"


@pytest.mark.asyncio
async def test_cancel_by_patient_updates_status_and_publishes(
    service: AppointmentService,
    repo: MagicMock,
    messaging: MagicMock,
    pubsub: MagicMock,
) -> None:
    """Cancelling an owned scheduled appointment should update and publish."""
    appointment = _make_appointment()
    cancelled = _make_appointment(status=AppointmentStatus.CANCELLED)
    repo.get_by_id.return_value = appointment
    repo.update_status.return_value = cancelled

    result = service.cancel_by_patient(appointment.id, PATIENT_ID)
    await asyncio.sleep(0)

    assert result is not None
    assert result.status == AppointmentStatus.CANCELLED
    repo.update_status.assert_called_once_with(appointment, AppointmentStatus.CANCELLED)
    messaging.get_pubsub.assert_called_once_with(APPOINTMENT_STATUS_CHANGED)
    pubsub.publish.assert_awaited_once()


def test_reschedule_returns_none_when_missing(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Rescheduling a missing appointment should return None."""
    repo.get_by_id.return_value = None

    result = service.reschedule(
        uuid.uuid4(),
        AppointmentRescheduleRequest(
            new_date=date(2026, 3, 11),
            new_time_preference=TimePreference.PM,
            new_hour=13,
        ),
    )

    assert result is None


def test_reschedule_raises_when_slot_taken(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Rescheduling into another appointment's slot should raise ValueError."""
    appointment = _make_appointment()
    taken = _make_appointment(assigned_time=time(13, 0))
    repo.get_by_id.return_value = appointment
    repo.get_by_doctor_date_and_preference.return_value = [taken]

    with pytest.raises(ValueError, match="already taken"):
        service.reschedule(
            appointment.id,
            AppointmentRescheduleRequest(
                new_date=date(2026, 3, 11),
                new_time_preference=TimePreference.PM,
                new_hour=13,
            ),
        )


@pytest.mark.asyncio
async def test_reschedule_saves_new_date_and_slot(
    service: AppointmentService,
    repo: MagicMock,
    messaging: MagicMock,
    pubsub: MagicMock,
) -> None:
    """Rescheduling should persist the appointment and publish status changed."""
    appointment = _make_appointment()
    repo.get_by_id.return_value = appointment
    repo.get_by_doctor_date_and_preference.return_value = []
    request = AppointmentRescheduleRequest(
        new_date=date(2026, 3, 11),
        new_time_preference=TimePreference.PM,
        new_hour=14,
    )

    result = service.reschedule(appointment.id, request)
    await asyncio.sleep(0)

    assert result is not None
    assert result.appointment_date == date(2026, 3, 11)
    assert result.time_preference == TimePreference.PM
    assert result.assigned_time == time(14, 0)
    repo.save.assert_called_once_with(appointment)
    messaging.get_pubsub.assert_called_once_with(APPOINTMENT_STATUS_CHANGED)
    pubsub.publish.assert_awaited_once()


def test_log_task_exception_handles_successful_task() -> None:
    """The task logger should not raise for a successful task."""
    task = MagicMock(spec=asyncio.Task)
    task.result.return_value = None

    AppointmentService._log_task_exception(task)

    task.result.assert_called_once()
