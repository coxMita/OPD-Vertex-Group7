"""Unit tests for the dev/demo appointment routes used by the /admin page."""

import uuid
from datetime import date, time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.api.routes.appointment_routes import (
    clear_db,
    list_all_appointments,
    start_session,
)
from src.models.db.appointment import Appointment, AppointmentStatus, TimePreference


def _appointment() -> Appointment:
    """Create a test appointment entity."""
    return Appointment(
        id=uuid.uuid4(),
        patient_id=uuid.uuid4(),
        doctor_id=uuid.uuid4(),
        appointment_date=date(2026, 11, 17),
        time_preference=TimePreference.AM,
        assigned_time=time(8, 0),
        status=AppointmentStatus.SCHEDULED,
    )


@pytest.mark.asyncio
async def test_list_all_appointments_passes_date_filter() -> None:
    """The date filter is forwarded to the repository and results are mapped."""
    entity = _appointment()
    with patch("src.api.routes.appointment_routes.AppointmentRepository") as repo_cls:
        repo_cls.return_value.get_all.return_value = [entity]
        result = await list_all_appointments(MagicMock(), date(2026, 11, 17))

    repo_cls.return_value.get_all.assert_called_once_with(date(2026, 11, 17))
    assert len(result) == 1
    assert result[0].id == entity.id


@pytest.mark.asyncio
async def test_start_session_triggers_notify_for_given_date() -> None:
    """start_session runs the scheduler job for the requested window."""
    with (
        patch("src.api.routes.appointment_routes.AppointmentRepository"),
        patch(
            "src.api.routes.appointment_routes._notify_session",
            new=AsyncMock(return_value=3),
        ) as notify,
    ):
        result = await start_session(MagicMock(), TimePreference.PM, date(2026, 11, 16))

    assert notify.await_args.args[2] == TimePreference.PM
    assert notify.await_args.args[3] == date(2026, 11, 16)
    assert result == {
        "time_preference": "PM",
        "appointment_date": "2026-11-16",
        "handed_off": 3,
    }


@pytest.mark.asyncio
async def test_start_session_defaults_to_today() -> None:
    """Without a date, the response reports today's date."""
    with (
        patch("src.api.routes.appointment_routes.AppointmentRepository"),
        patch(
            "src.api.routes.appointment_routes._notify_session",
            new=AsyncMock(return_value=0),
        ),
    ):
        result = await start_session(MagicMock(), TimePreference.AM)

    assert result["appointment_date"] == str(date.today())
    assert result["handed_off"] == 0


def test_clear_db_deletes_and_commits() -> None:
    """clear_db runs the delete and reports the deleted row count."""
    session = MagicMock()
    session.exec.return_value.rowcount = 5

    result = clear_db(session)

    session.commit.assert_called_once()
    assert result["deleted"] == 5  # noqa: PLR2004
