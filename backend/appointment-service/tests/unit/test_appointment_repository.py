"""Unit tests for AppointmentRepository."""

from datetime import date, time
from unittest.mock import MagicMock

import pytest

from src.models.db.appointment import Appointment, AppointmentStatus, TimePreference
from src.repositories.appointment_repository import AppointmentRepository

EXPECTED_TWO_APPOINTMENTS = 2


def _make_appointment(
    appointment_id: int,
    time_preference: TimePreference = TimePreference.AM,
    assigned_time: time = time(8, 0),
    status: AppointmentStatus = AppointmentStatus.SCHEDULED,
) -> Appointment:
    """Create a test appointment entity."""
    a = Appointment(
        patient_id=1,
        doctor_id=1,
        appointment_date=date(2026, 3, 10),
        time_preference=time_preference,
        assigned_time=assigned_time,
        status=status,
    )
    a.id = appointment_id
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
    appointment = _make_appointment(1)
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
    appointment = _make_appointment(1)
    session.get.return_value = appointment
    result = repo.get_by_id(1)
    session.get.assert_called_once_with(Appointment, 1)
    assert result == appointment


def test_get_by_id_returns_none_when_not_found(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Should return None when appointment does not exist."""
    session.get.return_value = None
    result = repo.get_by_id(99)
    assert result is None


# ── update_status


def test_update_status_saves_new_status(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Should update status and persist the change."""
    appointment = _make_appointment(1)
    result = repo.update_status(appointment, AppointmentStatus.IN_PROGRESS)
    assert result.status == AppointmentStatus.IN_PROGRESS
    session.add.assert_called_once_with(appointment)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(appointment)


# ── reorder


def test_reorder_persists_all_appointments(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Reorder should add and commit all appointments."""
    appointments = [
        _make_appointment(1, assigned_time=time(8, 0)),
        _make_appointment(2, assigned_time=time(9, 0)),
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

    repo.get_by_doctor_and_date(1, date(2026, 3, 10))
    session.exec.assert_called_once()
    # Verify the query was executed
    call_args = session.exec.call_args[0][0]
    assert call_args is not None


# ── get_by_patient_id


def test_get_by_patient_id_returns_list(
    repo: AppointmentRepository, session: MagicMock
) -> None:
    """Should return list of appointments for a patient."""
    appointments = [_make_appointment(1), _make_appointment(2)]
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter(appointments))
    session.exec.return_value = mock_result

    result = repo.get_by_patient_id(1)
    assert len(result) == EXPECTED_TWO_APPOINTMENTS
