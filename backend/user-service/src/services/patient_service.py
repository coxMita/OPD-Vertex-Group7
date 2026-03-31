from uuid import UUID

from src.models.db.patient import Patient
from src.models.dto.patient_create_request import PatientCreateRequest
from src.models.dto.patient_dto import PatientDTO
from src.repositories.patient_repository import PatientRepository


class PatientService:
    """Service for managing patients."""

    def __init__(self, repo: PatientRepository) -> None:
        """Initialize the PatientService."""
        self._repo = repo

    def find_or_create_patient(self, request: PatientCreateRequest) -> PatientDTO:
        """Find an existing patient by email or create a new one."""
        existing = self._repo.get_by_email(request.email)
        if existing:
            return self._to_dto(existing)

        patient = Patient(**request.model_dump())
        created = self._repo.create(patient)
        return self._to_dto(created)

    def get_patient(self, patient_id: UUID) -> PatientDTO | None:
        """Get a patient by ID."""
        patient = self._repo.get_by_id(patient_id)
        return self._to_dto(patient) if patient else None

    def _to_dto(self, patient: Patient) -> PatientDTO:
        """Convert a Patient entity to a PatientDTO."""
        return PatientDTO(**patient.model_dump())

    def get_patient_by_email(self, email: str) -> PatientDTO | None:
        """Get a patient by email address."""
        patient = self._repo.get_by_email(email)
        if patient is None:
            return None
        return self._to_dto(patient)
