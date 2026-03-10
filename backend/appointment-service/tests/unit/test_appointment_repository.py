"""Unit tests for AppointmentRepository."""

import uuid
from datetime import date, time
from unittest.mock import MagicMock

import pytest

from src.models.db.appointment import Appointment, AppointmentStatus, TimePreference
from src.repositories.appointment_repository import AppointmentRepository

EXPECTED_TWO_APPOINTMENTS = 2

DOCTOR_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")


def _make_appointment(
    appointment_id: uuid.UUID | None = None,
    time_preference: TimePreference = TimePreference.AM,
    assigned_time: time = time(8, 0),
    status: AppointmentStatus = AppointmentStatus.SCHEDULED,
) -> Appointment:
    """Create a test appointment entity."""
    a = Appointment(
        patient_id=uuid.uuid4(),
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        time_preference=time_preference,
        assigned_time=assigned_time,
        status=status,
    )
    a.id = appointment_id or uuid.uuid4()
    return a


@pytest.fixture
def session() -> MagicMock:
    """Return a mocked SQLModel Session."""
    return MagicMock()


@pytest.fixture
def repo(session: MagicMock) -> AppointmentRepository:
    """Return an AppointmentRepository with mocked session."""
    return AppointmentRepository(session)


# ── create


def test_create_saves_and_returns_appointment(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Create should add, commit and refresh the appointment."""
    appointment = _make_appointment()
    result = repo.create(appointment)
    session.add.assert_called_once_with(appointment)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(appointment)
    assert result == appointment


# ── get_by_id


def test_get_by_id_returns_appointment(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Should return appointment when found."""
    appointment_id = uuid.uuid4()
    appointment = _make_appointment(appointment_id)
    session.get.return_value = appointment
    result = repo.get_by_id(appointment_id)
    session.get.assert_called_once_with(Appointment, appointment_id)
    assert result == appointment


def test_get_by_id_returns_none_when_not_found(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Should return None when appointment does not exist."""
    session.get.return_value = None
    result = repo.get_by_id(uuid.uuid4())
    assert result is None


# ── update_status


def test_update_status_saves_new_status(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Should update status and persist the change."""
    appointment = _make_appointment()
    result = repo.update_status(appointment, AppointmentStatus.HANDED_OFF)
    assert result.status == AppointmentStatus.HANDED_OFF
    session.add.assert_called_once_with(appointment)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(appointment)


# ── reorder


def test_reorder_persists_all_appointments(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Reorder should add and commit all appointments."""
    appointments = [
        _make_appointment(assigned_time=time(8, 0)),
        _make_appointment(assigned_time=time(9, 0)),
    ]
    repo.reorder(appointments)
    assert session.add.call_count == EXPECTED_TWO_APPOINTMENTS
    session.commit.assert_called_once()


# ── get_by_doctor_and_date


def test_get_by_doctor_and_date_excludes_cancelled(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Should not include cancelled appointments in query."""
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([]))
    session.exec.return_value = mock_result

    repo.get_by_doctor_and_date(DOCTOR_ID, date(2026, 3, 10))
    session.exec.assert_called_once()
    call_args = session.exec.call_args[0][0]
    assert call_args is not None


# ── get_by_patient_id


def test_get_by_patient_id_returns_list(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Should return list of appointments for a patient."""
    appointments = [_make_appointment(), _make_appointment()]
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(appointments))
    session.exec.return_value = mock_result

    result = repo.get_by_patient_id(uuid.uuid4())
    assert len(result) == EXPECTED_TWO_APPOINTMENTS
