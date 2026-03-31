from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.api.dependencies import get_patient_service
from src.models.dto.patient_create_request import PatientCreateRequest
from src.models.dto.patient_dto import PatientDTO
from src.services.patient_service import PatientService

router = APIRouter(prefix="/api/v1/user/patients", tags=["patients"])


@router.post("", status_code=status.HTTP_201_CREATED)
def find_or_create_patient(
    request: PatientCreateRequest,
    service: Annotated[PatientService, Depends(get_patient_service)],
) -> PatientDTO:
    """Find or create a patient."""
    return service.find_or_create_patient(request)


# IMPORTANT: /by-email must be before /{patient_id} to avoid UUID parse conflict
@router.get("/by-email", status_code=status.HTTP_200_OK)
def get_patient_by_email(
    email: str,
    service: Annotated[PatientService, Depends(get_patient_service)],
    response: Response,
) -> PatientDTO | dict[str, str]:
    """Get a patient by email address."""
    patient = service.get_patient_by_email(email)
    if patient is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Patient not found"}
    return patient


@router.get("/{patient_id}", status_code=status.HTTP_200_OK)
def get_patient(
    patient_id: UUID,
    service: Annotated[PatientService, Depends(get_patient_service)],
    response: Response,
) -> PatientDTO | dict[str, str]:
    """Get a patient by ID."""
    patient = service.get_patient(patient_id)
    if patient is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Patient not found"}
    return patient
