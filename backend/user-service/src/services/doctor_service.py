from uuid import UUID

from src.models.db.doctor import Doctor
from src.models.dto.doctor_dto import DoctorDTO
from src.repositories.doctor_repository import DoctorRepository


class DoctorService:
    """Service for managing doctors."""

    def __init__(self, repo: DoctorRepository) -> None:
        """Initialize the DoctorService."""
        self._repo = repo

    def list_all_doctors(self) -> list[DoctorDTO]:
        """Get all doctors."""
        doctors = self._repo.get_all()
        return [self._to_dto(d) for d in doctors]

    def create_doctor(self, doctor_data: dict) -> DoctorDTO:
        """Create a new doctor."""
        doctor = Doctor(**doctor_data)
        created = self._repo.create(doctor)
        return self._to_dto(created)

    def get_doctors_by_department(self, department_name: str) -> list[DoctorDTO]:
        """Get all doctors in a specific department."""
        doctors = self._repo.get_all_by_department(department_name)
        return [self._to_dto(d) for d in doctors]

    def get_doctor(self, doctor_id: UUID) -> DoctorDTO | None:
        """Get a doctor by ID."""
        doctor = self._repo.get_by_id(doctor_id)
        return self._to_dto(doctor) if doctor else None

    def _to_dto(self, doctor: Doctor) -> DoctorDTO:
        """Convert a Doctor entity to a DoctorDTO."""
        return DoctorDTO(**doctor.model_dump())
