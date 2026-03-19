"""API routes for consultations."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.api.dependencies import get_consultation_service
from src.models.dto.consultation_create_request import ConsultationCreateRequest
from src.models.dto.consultation_response import ConsultationResponse
from src.models.dto.consultation_status_update_request import (
    ConsultationUpdateRequest,
)
from src.services.consultation_service import ConsultationService

MESSAGE = "message"
NOT_FOUND_MESSAGE = "Consultation not found"

router = APIRouter(prefix="/api/v1/consultations", tags=["consultations"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_consultation(
    request: ConsultationCreateRequest,
    service: Annotated[ConsultationService, Depends(get_consultation_service)],
    response: Response,
) -> ConsultationResponse | dict:
    """Create a new consultation session.

    Args:
        request (ConsultationCreateRequest): The consultation request.
        service (ConsultationService): The consultation service.
        response (Response): The FastAPI response object.

    Returns:
        ConsultationResponse: The created consultation.

    """
    try:
        return service.create_consultation(request)
    except ValueError as e:
        response.status_code = status.HTTP_409_CONFLICT
        return {MESSAGE: str(e)}


@router.get("/{consultation_id}", status_code=status.HTTP_200_OK)
async def get_consultation(
    consultation_id: uuid.UUID,
    service: Annotated[ConsultationService, Depends(get_consultation_service)],
    response: Response,
) -> ConsultationResponse | dict:
    """Get a specific consultation by ID.

    Args:
        consultation_id (uuid.UUID): The consultation ID.
        service (ConsultationService): The consultation service.
        response (Response): The FastAPI response object.

    Returns:
        ConsultationResponse: The consultation details.

    """
    consultation = service.get_consultation(consultation_id)
    if consultation is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}
    return consultation


@router.get("/appointment/{appointment_id}", status_code=status.HTTP_200_OK)
async def get_consultation_by_appointment(
    appointment_id: uuid.UUID,
    service: Annotated[ConsultationService, Depends(get_consultation_service)],
    response: Response,
) -> ConsultationResponse | dict:
    """Get a consultation by appointment ID.

    Args:
        appointment_id (uuid.UUID): The appointment ID.
        service (ConsultationService): The consultation service.
        response (Response): The FastAPI response object.

    Returns:
        ConsultationResponse: The consultation details.

    """
    consultation = service.get_by_appointment_id(appointment_id)
    if consultation is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}
    return consultation


@router.get("/doctor/{doctor_id}", status_code=status.HTTP_200_OK)
async def get_doctor_consultations(
    doctor_id: uuid.UUID,
    service: Annotated[ConsultationService, Depends(get_consultation_service)],
) -> list[ConsultationResponse]:
    """Get all consultations for a doctor.

    Args:
        doctor_id (uuid.UUID): The doctor's ID.
        service (ConsultationService): The consultation service.

    Returns:
        list[ConsultationResponse]: The doctor's consultations.

    """
    return service.get_doctor_consultations(doctor_id)


@router.patch("/{consultation_id}", status_code=status.HTTP_200_OK)
async def update_consultation(
    consultation_id: uuid.UUID,
    request: ConsultationUpdateRequest,
    service: Annotated[ConsultationService, Depends(get_consultation_service)],
    response: Response,
) -> ConsultationResponse | dict:
    """Update a consultation.

    Args:
        consultation_id (uuid.UUID): The consultation ID.
        request (ConsultationUpdateRequest): The update request.
        service (ConsultationService): The consultation service.
        response (Response): The FastAPI response object.

    Returns:
        ConsultationResponse: The updated consultation.

    """
    result = service.update_consultation(consultation_id, request)
    if result is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}
    return result
