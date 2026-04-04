"""API routes for prescriptions."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.api.dependencies import get_prescription_service
from src.models.dto.prescription_response import PrescriptionResponse
from src.services.prescription_service import PrescriptionService

MESSAGE = "message"
NOT_FOUND_MESSAGE = "Prescription not found"

router = APIRouter(prefix="/api/v1/prescriptions", tags=["prescriptions"])


@router.get("/consultation/{consultation_id}", status_code=status.HTTP_200_OK)
async def get_prescription_by_consultation(
    consultation_id: uuid.UUID,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    response: Response,
) -> PrescriptionResponse | dict:
    """Get the most recent prescription for a consultation.

    Args:
        consultation_id: The consultation UUID.
        service: The prescription service.
        response: The FastAPI response object.

    Returns:
        PrescriptionResponse: The prescription details.

    """
    prescription = service.get_by_consultation_id(consultation_id)
    if prescription is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}
    return prescription


@router.get("/{prescription_id}", status_code=status.HTTP_200_OK)
async def get_prescription(
    prescription_id: uuid.UUID,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    response: Response,
) -> PrescriptionResponse | dict:
    """Get a prescription by ID.

    Args:
        prescription_id: The prescription UUID.
        service: The prescription service.
        response: The FastAPI response object.

    Returns:
        PrescriptionResponse: The prescription details.

    """
    prescription = service.get_by_id(prescription_id)
    if prescription is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}
    return prescription


@router.get("/patient/{patient_id}", status_code=status.HTTP_200_OK)
async def get_patient_prescriptions(
    patient_id: uuid.UUID,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
) -> list[PrescriptionResponse]:
    """Get all prescriptions for a patient.

    Args:
        patient_id: The patient UUID.
        service: The prescription service.

    Returns:
        list[PrescriptionResponse]: The patient's prescriptions.

    """
    return service.get_by_patient_id(patient_id)


@router.patch("/{prescription_id}/approve", status_code=status.HTTP_200_OK)
async def approve_prescription(
    prescription_id: uuid.UUID,
    service: Annotated[PrescriptionService, Depends(get_prescription_service)],
    response: Response,
) -> PrescriptionResponse | dict:
    """Approve a prescription.

    Args:
        prescription_id: The prescription UUID.
        service: The prescription service.
        response: The FastAPI response object.

    Returns:
        PrescriptionResponse: The updated prescription.

    """
    result = service.approve(prescription_id)
    if result is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: NOT_FOUND_MESSAGE}
    return result
