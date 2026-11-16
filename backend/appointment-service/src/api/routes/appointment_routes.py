"""API routes for appointments."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlmodel import Session

from src.api.dependencies import get_appointment_service, get_db_session
from src.messaging.messaging_manager import messaging_manager
from src.models.db.appointment import TimePreference
from src.models.dto.appointment_create_request import AppointmentCreateRequest
from src.models.dto.appointment_reschedule_request import AppointmentRescheduleRequest
from src.models.dto.appointment_response import AppointmentResponse
from src.models.dto.appointment_status_update_request import (
    AppointmentStatusUpdateRequest,
)
from src.models.dto.queue_reorder_request import QueueReorderRequest
from src.repositories.appointment_repository import AppointmentRepository
from src.scheduling.appointment_scheduler import _notify_session
from src.services.appointment_service import AppointmentService

MESSAGE = "message"
NOT_FOUND_MESSAGE = "Appointment not found"

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_appointment(
    request: AppointmentCreateRequest,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    response: Response,
) -> AppointmentResponse | dict:
    """Book a new appointment.

    Args:
        request (AppointmentCreateRequest): The booking request.
        service (AppointmentService): The appointment service.
        response (Response): The FastAPI response object.

    Returns:
        AppointmentResponse: The created appointment.

    """
    try:
        return service.create_appointment(request)
    except ValueError as e:
        response.status_code = status.HTTP_409_CONFLICT
        return {MESSAGE: str(e)}


@router.get("/{appointment_id}", status_code=status.HTTP_200_OK)
async def get_appointment(
    appointment_id: uuid.UUID,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    response: Response,
) -> AppointmentResponse | dict:
    """Get a specific appointment by ID.

    Args:
        appointment_id (uuid.UUID): The appointment ID.
        service (AppointmentService): The appointment service.
        response (Response): The FastAPI response object.

    Returns:
        AppointmentResponse: The appointment details.

    """
    appointment = service.get_appointment(appointment_id)
    if appointment is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}
    return appointment


@router.get("/queue/day", status_code=status.HTTP_200_OK)
async def get_queue(
    doctor_id: uuid.UUID,
    appointment_date: date,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
) -> list[AppointmentResponse]:
    """Get the ordered queue for a doctor on a specific date.

    Args:
        doctor_id (uuid.UUID): The doctor's ID.
        appointment_date (date): The date of the session.
        service (AppointmentService): The appointment service.

    Returns:
        list[AppointmentResponse]: Appointments ordered by assigned time.

    """
    return service.get_queue(doctor_id, appointment_date)


@router.get("/patient/{patient_id}", status_code=status.HTTP_200_OK)
async def get_patient_appointments(
    patient_id: uuid.UUID,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
) -> list[AppointmentResponse]:
    """Get all appointments for a patient.

    Args:
        patient_id (uuid.UUID): The patient's ID.
        service (AppointmentService): The appointment service.

    Returns:
        list[AppointmentResponse]: The patient's appointments.

    """
    return service.get_patient_appointments(patient_id)


@router.patch("/{appointment_id}/status", status_code=status.HTTP_200_OK)
async def update_status(
    appointment_id: uuid.UUID,
    request: AppointmentStatusUpdateRequest,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    response: Response,
) -> AppointmentResponse | dict:
    """Update the status of an appointment.

    Args:
        appointment_id (uuid.UUID): The appointment ID.
        request (AppointmentStatusUpdateRequest): The new status.
        service (AppointmentService): The appointment service.
        response (Response): The FastAPI response object.

    Returns:
        AppointmentResponse: The updated appointment.

    """
    result = service.update_status(appointment_id, request)
    if result is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}
    return result


@router.patch("/queue/reorder", status_code=status.HTTP_200_OK)
async def reorder_queue(
    doctor_id: uuid.UUID,
    appointment_date: date,
    request: QueueReorderRequest,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    response: Response,
) -> list[AppointmentResponse] | dict:
    """Reorder the appointment queue for a doctor session.

    Args:
        doctor_id (uuid.UUID): The doctor's ID.
        appointment_date (date): The date of the session.
        request (QueueReorderRequest): Ordered list of appointment IDs.
        service (AppointmentService): The appointment service.
        response (Response): The FastAPI response object.

    Returns:
        list[AppointmentResponse]: The reordered appointments.

    """
    try:
        return service.reorder_queue(doctor_id, appointment_date, request)
    except ValueError as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {MESSAGE: str(e)}


@router.patch("/{appointment_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_appointment(
    appointment_id: uuid.UUID,
    patient_id: uuid.UUID,  # query param — verificare ownership
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    response: Response,
) -> AppointmentResponse | dict:
    """Cancel an appointment by the patient who owns it."""
    result = service.cancel_by_patient(appointment_id, patient_id)
    if result is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}
    if result == "forbidden":
        response.status_code = status.HTTP_403_FORBIDDEN
        return {MESSAGE: "You can only cancel your own appointments."}
    if result == "conflict":
        response.status_code = status.HTTP_409_CONFLICT
        return {MESSAGE: "Only scheduled appointments can be cancelled."}
    return result


@router.patch("/{appointment_id}/reschedule", status_code=status.HTTP_200_OK)
async def reschedule_appointment(
    appointment_id: uuid.UUID,
    request: AppointmentRescheduleRequest,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    response: Response,
) -> AppointmentResponse | dict:
    """Move an appointment to a different date/time slot."""
    try:
        result = service.reschedule(appointment_id, request)
    except ValueError as e:
        response.status_code = status.HTTP_409_CONFLICT
        return {MESSAGE: str(e)}

    if result is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}

    return result


# ── Dev / demo helpers ───────────────────────────────────────────────────────
# Used by the frontend /admin page to drive a demo without waiting for cron.


@router.get("/dev/all", status_code=status.HTTP_200_OK)
async def list_all_appointments(
    session: Annotated[Session, Depends(get_db_session)],
    appointment_date: date | None = None,
) -> list[AppointmentResponse]:
    """List every appointment, optionally filtered by date (dev only)."""
    repo = AppointmentRepository(session)
    return [AppointmentResponse.from_entity(a) for a in repo.get_all(appointment_date)]


@router.post("/dev/start-session", status_code=status.HTTP_200_OK)
async def start_session(
    session: Annotated[Session, Depends(get_db_session)],
    time_preference: TimePreference,
    appointment_date: date | None = None,
) -> dict:
    """Run the AM/PM session job now instead of waiting for the cron (dev only).

    Publishes session_started (consultation-service creates the consultations)
    and marks the appointments as handed_off.
    """
    count = await _notify_session(
        AppointmentRepository(session),
        messaging_manager,
        time_preference,
        appointment_date,
    )
    return {
        "time_preference": time_preference.value,
        "appointment_date": str(appointment_date or date.today()),
        "handed_off": count,
    }


@router.delete("/dev", status_code=status.HTTP_200_OK)
def clear_db(session: Annotated[Session, Depends(get_db_session)]) -> dict:
    """Delete every appointment (dev only)."""
    result = session.exec(text("DELETE FROM appointment"))
    session.commit()
    return {MESSAGE: "Appointments cleared", "deleted": result.rowcount}
