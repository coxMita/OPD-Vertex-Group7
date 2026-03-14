"""Unit tests for AppointmentService."""

import uuid
from datetime import date, time
from unittest.mock import MagicMock

import pytest

from src.models.db.appointment import Appointment, AppointmentStatus, TimePreference
from src.models.dto.appointment_create_request import AppointmentCreateRequest
from src.models.dto.appointment_status_update_request import (
    AppointmentStatusUpdateRequest,
)
from src.models.dto.queue_reorder_request import QueueReorderRequest
from src.services.appointment_service import AppointmentService

DOCTOR_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
PATIENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _make_appointment(
    appointment_id: uuid.UUID | None = None,
    doctor_id: uuid.UUID = DOCTOR_ID,
    time_preference: TimePreference = TimePreference.AM,
    assigned_time: time = time(8, 0),
    status: AppointmentStatus = AppointmentStatus.SCHEDULED,
) -> Appointment:
    """Create a test appointment entity."""
    a = Appointment(
        patient_id=PATIENT_ID,
        doctor_id=doctor_id,
        appointment_date=date(2026, 3, 10),
        time_preference=time_preference,
        assigned_time=assigned_time,
        status=status,
    )
    a.id = appointment_id or uuid.uuid4()
    return a


class DummyPubSub:
    """Stub for PubSubFacade."""

    def publish(self, message: object) -> None:
        """Do nothing."""


class DummyMessaging:
    """Stub for MessagingManager."""

    @staticmethod
    def get_pubsub(exchange_name: str) -> "DummyPubSub":
        """Return a dummy pubsub."""
        return DummyPubSub()


@pytest.fixture
def repo() -> MagicMock:
    """Return a mocked AppointmentRepository."""
    return MagicMock()


@pytest.fixture
def service(repo: MagicMock) -> AppointmentService:
    """Return an AppointmentService with mocked dependencies."""
    return AppointmentService(repo, DummyMessaging())


# ── Slot assignment


def test_create_appointment_assigns_first_am_slot(
    service: AppointmentService, repo: MagicMock
) -> None:
    """First AM booking should get 08:00."""
    repo.get_by_doctor_date_and_preference.return_value = []
    appointment = _make_appointment(assigned_time=time(8, 0))
    repo.create.return_value = appointment

    request = AppointmentCreateRequest(
        patient_id=PATIENT_ID,
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        time_preference=TimePreference.AM,
    )
    result = service.create_appointment(request)
    assert result.assigned_time == time(8, 0)


def test_create_appointment_assigns_next_available_slot(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Second AM booking should get 09:00 if 08:00 is taken."""
    existing = _make_appointment(assigned_time=time(8, 0))
    repo.get_by_doctor_date_and_preference.return_value = [existing]
    appointment = _make_appointment(assigned_time=time(9, 0))
    repo.create.return_value = appointment

    request = AppointmentCreateRequest(
        patient_id=PATIENT_ID,
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        time_preference=TimePreference.AM,
    )
    result = service.create_appointment(request)
    assert result.assigned_time == time(9, 0)


def test_create_appointment_raises_when_no_slots_available(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Should raise ValueError when all AM slots are taken."""
    existing = [_make_appointment(assigned_time=time(8 + i, 0)) for i in range(4)]
    repo.get_by_doctor_date_and_preference.return_value = existing

    request = AppointmentCreateRequest(
        patient_id=PATIENT_ID,
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        time_preference=TimePreference.AM,
    )
    with pytest.raises(ValueError):
        service.create_appointment(request)


def test_create_appointment_assigns_first_pm_slot(
    service: AppointmentService, repo: MagicMock
) -> None:
    """First PM booking should get 13:00."""
    repo.get_by_doctor_date_and_preference.return_value = []
    appointment = _make_appointment(
        time_preference=TimePreference.PM, assigned_time=time(13, 0)
    )
    repo.create.return_value = appointment

    request = AppointmentCreateRequest(
        patient_id=PATIENT_ID,
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        time_preference=TimePreference.PM,
    )
    result = service.create_appointment(request)
    assert result.assigned_time == time(13, 0)


# ── Status update


def test_update_status_returns_none_when_not_found(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Should return None if appointment does not exist."""
    repo.get_by_id.return_value = None
    result = service.update_status(
        uuid.uuid4(), AppointmentStatusUpdateRequest(status=AppointmentStatus.COMPLETED)
    )
    assert result is None


def test_update_status_updates_correctly(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Should return updated appointment with new status."""
    appointment_id = uuid.uuid4()
    appointment = _make_appointment(appointment_id)
    updated = _make_appointment(appointment_id, status=AppointmentStatus.HANDED_OFF)
    repo.get_by_id.return_value = appointment
    repo.update_status.return_value = updated

    result = service.update_status(
        appointment_id,
        AppointmentStatusUpdateRequest(status=AppointmentStatus.HANDED_OFF),
    )
    assert result.status == AppointmentStatus.HANDED_OFF


# ── Queue reorder


def test_reorder_queue_reassigns_am_slots(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Reordering should reassign time slots in requested order."""
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    a1 = _make_appointment(id1, assigned_time=time(8, 0))
    a2 = _make_appointment(id2, assigned_time=time(9, 0))
    repo.get_by_doctor_and_date.return_value = [a1, a2]
    repo.reorder.return_value = [a2, a1]

    service.reorder_queue(
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        request=QueueReorderRequest(appointment_ids=[id2, id1]),
    )
    repo.reorder.assert_called_once()
    reordered = repo.reorder.call_args[0][0]
    assert reordered[0].assigned_time == time(8, 0)
    assert reordered[1].assigned_time == time(9, 0)


def test_reorder_queue_raises_on_invalid_ids(
    service: AppointmentService, repo: MagicMock
) -> None:
    """Should raise ValueError if appointment_ids don't match active appointments."""
    id1 = uuid.uuid4()
    id2 = uuid.uuid4()
    a1 = _make_appointment(id1)
    a2 = _make_appointment(id2)
    repo.get_by_doctor_and_date.return_value = [a1, a2]

    with pytest.raises(ValueError):
        service.reorder_queue(
            doctor_id=DOCTOR_ID,
            appointment_date=date(2026, 3, 10),
            request=QueueReorderRequest(appointment_ids=[id1, uuid.uuid4()]),
        )
