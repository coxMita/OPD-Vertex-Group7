from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from src.api.auth import get_current_user
from src.api.dependencies import get_doctor_service
from src.models.dto.doctor_dto import DoctorDTO
from src.services.doctor_service import DoctorService

router = APIRouter(prefix="/api/v1/user", tags=["doctors"])


@router.get("/doctor/{department_name}/doctors", status_code=status.HTTP_200_OK)
def get_doctors_by_department(
    department_name: str,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
    user_claims: Annotated[dict, Depends(get_current_user)],
) -> list[DoctorDTO]:
    """Get all doctors in a specific department."""
    return service.get_doctors_by_department(department_name)


@router.get("/doctors/{doctor_id}", status_code=status.HTTP_200_OK)
def get_doctor(
    doctor_id: UUID,
    service: Annotated[DoctorService, Depends(get_doctor_service)],
    user_claims: Annotated[dict, Depends(get_current_user)],
    response: Response,
) -> DoctorDTO | dict[str, str]:
    """Get a doctor by ID."""
    doctor = service.get_doctor(doctor_id)
    if doctor is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "Doctor not found"}
    return doctor
