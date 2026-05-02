"""Unit tests for appointment route handlers."""

import uuid
from datetime import date, time
from unittest.mock import MagicMock

import pytest
from fastapi import Response, status

from src.api.routes.appointment_routes import (
    cancel_appointment,
    create_appointment,
    get_appointment,
    get_patient_appointments,
    get_queue,
    reorder_queue,
    reschedule_appointment,
    update_status,
)
from src.models.db.appointment import AppointmentStatus, TimePreference
from src.models.dto.appointment_create_request import AppointmentCreateRequest
from src.models.dto.appointment_reschedule_request import AppointmentRescheduleRequest
from src.models.dto.appointment_response import AppointmentResponse
from src.models.dto.appointment_status_update_request import (
    AppointmentStatusUpdateRequest,
)
from src.models.dto.queue_reorder_request import QueueReorderRequest

APPOINTMENT_ID = uuid.UUID("00000000-0000-0000-0002-000000000001")
DOCTOR_ID = uuid.UUID("00000000-0000-0000-0001-000000000001")
PATIENT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _response(
    status_value: AppointmentStatus = AppointmentStatus.SCHEDULED,
) -> AppointmentResponse:
    """Create a test appointment response DTO."""
    return AppointmentResponse(
        id=APPOINTMENT_ID,
        patient_id=PATIENT_ID,
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        time_preference=TimePreference.AM,
        assigned_time=time(8, 0),
        status=status_value,
        notes=None,
    )


def _create_request() -> AppointmentCreateRequest:
    """Create a test appointment create request."""
    return AppointmentCreateRequest(
        patient_id=PATIENT_ID,
        doctor_id=DOCTOR_ID,
        appointment_date=date(2026, 3, 10),
        time_preference=TimePreference.AM,
    )


@pytest.mark.asyncio
async def test_create_appointment_route_returns_created_response() -> None:
    """The create route should return a service response."""
    service = MagicMock()
    service.create_appointment.return_value = _response()
    response = Response()

    result = await create_appointment(_create_request(), service, response)

    assert result == _response()
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_create_appointment_route_returns_conflict() -> None:
    """The create route should translate slot conflicts to HTTP 409."""
    service = MagicMock()
    service.create_appointment.side_effect = ValueError("full")
    response = Response()

    result = await create_appointment(_create_request(), service, response)

    assert result == {"message": "full"}
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_get_appointment_route_returns_not_found() -> None:
    """The get route should translate a missing appointment to HTTP 404."""
    service = MagicMock()
    service.get_appointment.return_value = None
    response = Response()

    result = await get_appointment(APPOINTMENT_ID, service, response)

    assert result == {"message": "Appointment not found"}
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_appointment_route_returns_appointment() -> None:
    """The get route should return an appointment when it exists."""
    service = MagicMock()
    service.get_appointment.return_value = _response()
    response = Response()

    result = await get_appointment(APPOINTMENT_ID, service, response)

    assert result == _response()


@pytest.mark.asyncio
async def test_get_queue_route_delegates_to_service() -> None:
    """The queue route should delegate doctor and date filters."""
    service = MagicMock()
    service.get_queue.return_value = [_response()]

    result = await get_queue(DOCTOR_ID, date(2026, 3, 10), service)

    assert result == [_response()]
    service.get_queue.assert_called_once_with(DOCTOR_ID, date(2026, 3, 10))


@pytest.mark.asyncio
async def test_get_patient_appointments_route_delegates_to_service() -> None:
    """The patient route should delegate patient lookup."""
    service = MagicMock()
    service.get_patient_appointments.return_value = [_response()]

    result = await get_patient_appointments(PATIENT_ID, service)

    assert result == [_response()]
    service.get_patient_appointments.assert_called_once_with(PATIENT_ID)


@pytest.mark.asyncio
async def test_update_status_route_returns_not_found() -> None:
    """The status route should translate missing appointments to HTTP 404."""
    service = MagicMock()
    service.update_status.return_value = None
    response = Response()
    request = AppointmentStatusUpdateRequest(status=AppointmentStatus.COMPLETED)

    result = await update_status(APPOINTMENT_ID, request, service, response)

    assert result == {"message": "Appointment not found"}
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_status_route_returns_updated_response() -> None:
    """The status route should return updated appointments."""
    service = MagicMock()
    service.update_status.return_value = _response(AppointmentStatus.COMPLETED)
    response = Response()
    request = AppointmentStatusUpdateRequest(status=AppointmentStatus.COMPLETED)

    result = await update_status(APPOINTMENT_ID, request, service, response)

    assert result == _response(AppointmentStatus.COMPLETED)


@pytest.mark.asyncio
async def test_reorder_queue_route_returns_bad_request() -> None:
    """The reorder route should translate invalid IDs to HTTP 400."""
    service = MagicMock()
    service.reorder_queue.side_effect = ValueError("bad ids")
    response = Response()
    request = QueueReorderRequest(appointment_ids=[APPOINTMENT_ID])

    result = await reorder_queue(
        DOCTOR_ID, date(2026, 3, 10), request, service, response
    )

    assert result == {"message": "bad ids"}
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_reorder_queue_route_returns_reordered_response() -> None:
    """The reorder route should return the reordered appointments."""
    service = MagicMock()
    service.reorder_queue.return_value = [_response()]
    response = Response()
    request = QueueReorderRequest(appointment_ids=[APPOINTMENT_ID])

    result = await reorder_queue(
        DOCTOR_ID, date(2026, 3, 10), request, service, response
    )

    assert result == [_response()]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("service_result", "expected_status", "expected_message"),
    [
        (None, status.HTTP_404_NOT_FOUND, "Appointment not found"),
        (
            "forbidden",
            status.HTTP_403_FORBIDDEN,
            "You can only cancel your own appointments.",
        ),
        (
            "conflict",
            status.HTTP_409_CONFLICT,
            "Only scheduled appointments can be cancelled.",
        ),
    ],
)
async def test_cancel_appointment_route_handles_error_results(
    service_result: str | None,
    expected_status: int,
    expected_message: str,
) -> None:
    """The cancel route should map service sentinel values to HTTP errors."""
    service = MagicMock()
    service.cancel_by_patient.return_value = service_result
    response = Response()

    result = await cancel_appointment(APPOINTMENT_ID, PATIENT_ID, service, response)

    assert result == {"message": expected_message}
    assert response.status_code == expected_status


@pytest.mark.asyncio
async def test_cancel_appointment_route_returns_cancelled_response() -> None:
    """The cancel route should return a cancelled appointment response."""
    service = MagicMock()
    service.cancel_by_patient.return_value = _response(AppointmentStatus.CANCELLED)
    response = Response()

    result = await cancel_appointment(APPOINTMENT_ID, PATIENT_ID, service, response)

    assert result == _response(AppointmentStatus.CANCELLED)


@pytest.mark.asyncio
async def test_reschedule_appointment_route_returns_conflict() -> None:
    """The reschedule route should translate taken slots to HTTP 409."""
    service = MagicMock()
    service.reschedule.side_effect = ValueError("taken")
    response = Response()
    request = AppointmentRescheduleRequest(
        new_date=date(2026, 3, 11),
        new_time_preference=TimePreference.PM,
        new_hour=13,
    )

    result = await reschedule_appointment(APPOINTMENT_ID, request, service, response)

    assert result == {"message": "taken"}
    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_reschedule_appointment_route_returns_not_found() -> None:
    """The reschedule route should translate missing appointments to HTTP 404."""
    service = MagicMock()
    service.reschedule.return_value = None
    response = Response()
    request = AppointmentRescheduleRequest(
        new_date=date(2026, 3, 11),
        new_time_preference=TimePreference.PM,
        new_hour=13,
    )

    result = await reschedule_appointment(APPOINTMENT_ID, request, service, response)

    assert result == {"message": "Appointment not found"}
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_reschedule_appointment_route_returns_response() -> None:
    """The reschedule route should return a successful service response."""
    service = MagicMock()
    service.reschedule.return_value = _response()
    response = Response()
    request = AppointmentRescheduleRequest(
        new_date=date(2026, 3, 11),
        new_time_preference=TimePreference.PM,
        new_hour=13,
    )

    result = await reschedule_appointment(APPOINTMENT_ID, request, service, response)

    assert result == _response()
