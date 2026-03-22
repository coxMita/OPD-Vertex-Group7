"""API routes for patients."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.api.dependencies import get_patient_service
from src.models.dto.patient_dto import PatientFindOrCreateRequest, PatientResponse
from src.services.user_service import PatientService

MESSAGE = "message"
router = APIRouter(prefix="/api/v1/users/patients", tags=["patients"])


@router.post("", status_code=status.HTTP_200_OK)
async def find_or_create_patient(
    request: PatientFindOrCreateRequest,
    service: Annotated[PatientService, Depends(get_patient_service)],
) -> PatientResponse:
    """Find an existing patient by email or create a new one.

    Args:
        request (PatientFindOrCreateRequest): The patient data.
        service (PatientService): The patient service.

    Returns:
        PatientResponse: The found or created patient.

    """
    return service.find_or_create(request)


@router.get("/lookup", status_code=status.HTTP_200_OK)
async def lookup_patient_by_email(
    email: str,
    service: Annotated[PatientService, Depends(get_patient_service)],
    response: Response,
) -> PatientResponse | dict:
    """Look up a patient by email address.

    Args:
        email (str): The patient's email.
        service (PatientService): The patient service.
        response (Response): The FastAPI response object.

    Returns:
        PatientResponse: The patient details, or 404 if not found.

    """
    patient = service.get_patient_by_email(email)
    if patient is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: "Patient not found"}
    return patient


@router.get("/{patient_id}", status_code=status.HTTP_200_OK)
async def get_patient(
    patient_id: uuid.UUID,
    service: Annotated[PatientService, Depends(get_patient_service)],
    response: Response,
) -> PatientResponse | dict:
    """Get a patient by ID.

    Args:
        patient_id (uuid.UUID): The patient's ID.
        service (PatientService): The patient service.
        response (Response): The FastAPI response object.

    Returns:
        PatientResponse: The patient details.

    """
    patient = service.get_patient(patient_id)
    if patient is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: "Patient not found"}
    return patient
