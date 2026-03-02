"""API routes for appointments."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.api.dependencies import get_appointment_service
from src.models.dto.appointment_create_request import AppointmentCreateRequest
from src.models.dto.appointment_response import AppointmentResponse
from src.models.dto.appointment_status_update_request import (
    AppointmentStatusUpdateRequest,
)
from src.models.dto.queue_reorder_request import QueueReorderRequest
from src.services.appointment_service import AppointmentService

MESSAGE = "message"
NOT_FOUND_MESSAGE = "Appointment not found"

router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_appointment(
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
def get_appointment(
    appointment_id: int,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    response: Response,
) -> AppointmentResponse | dict:
    """Get a specific appointment by ID.

    Args:
        appointment_id (int): The appointment ID.
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
def get_queue(
    doctor_id: int,
    appointment_date: date,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
) -> list[AppointmentResponse]:
    """Get the ordered queue for a doctor on a specific date.

    Args:
        doctor_id (int): The doctor's ID.
        appointment_date (date): The date of the session.
        service (AppointmentService): The appointment service.

    Returns:
        list[AppointmentResponse]: Appointments ordered by assigned time.

    """
    return service.get_queue(doctor_id, appointment_date)


@router.get("/patient/{patient_id}", status_code=status.HTTP_200_OK)
def get_patient_appointments(
    patient_id: int,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
) -> list[AppointmentResponse]:
    """Get all appointments for a patient.

    Args:
        patient_id (int): The patient's ID.
        service (AppointmentService): The appointment service.

    Returns:
        list[AppointmentResponse]: The patient's appointments.

    """
    return service.get_patient_appointments(patient_id)


@router.patch("/{appointment_id}/status", status_code=status.HTTP_200_OK)
def update_status(
    appointment_id: int,
    request: AppointmentStatusUpdateRequest,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    response: Response,
) -> AppointmentResponse | dict:
    """Update the status of an appointment.

    Args:
        appointment_id (int): The appointment ID.
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
def reorder_queue(
    doctor_id: int,
    appointment_date: date,
    request: QueueReorderRequest,
    service: Annotated[AppointmentService, Depends(get_appointment_service)],
    response: Response,
) -> list[AppointmentResponse] | dict:
    """Reorder the appointment queue for a doctor session.

    Args:
        doctor_id (int): The doctor's ID.
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
