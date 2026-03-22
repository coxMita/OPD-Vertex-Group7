"""API routes for doctors."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from src.api.dependencies import get_doctor_service
from src.models.dto.doctor_dto import DoctorResponse
from src.services.user_service import DoctorService

MESSAGE = "message"
router = APIRouter(prefix="/api/v1/users/doctors", tags=["doctors"])


@router.get("", status_code=status.HTTP_200_OK)
async def get_all_doctors(
    service: Annotated[DoctorService, Depends(get_doctor_service)],
) -> list[DoctorResponse]:
    """Get all doctors.

    Args:
        service (DoctorService): The doctor service.

    Returns:
        list[DoctorResponse]: All doctors.

    """
    return service.get_all_doctors()


@router.get("/{doctor_id}", status_code=status.HTTP_200_OK)
async def get_doctor(
    doctor_id: uuid.UUID,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
    response: Response,
) -> DoctorResponse | dict:
    """Get a doctor by ID.

    Args:
        doctor_id (uuid.UUID): The doctor's ID.
        service (DoctorService): The doctor service.
        response (Response): The FastAPI response object.

    Returns:
        DoctorResponse: The doctor details.

    """
    doctor = service.get_doctor(doctor_id)
    if doctor is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {MESSAGE: "Doctor not found"}
    return doctor
