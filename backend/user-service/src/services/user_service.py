"""User service — business logic for patients and doctors."""

import logging
import uuid

from src.models.db.user import Patient
from src.models.dto.doctor_dto import DoctorResponse
from src.models.dto.patient_dto import PatientFindOrCreateRequest, PatientResponse
from src.repositories.user_repository import DoctorRepository, PatientRepository

logger = logging.getLogger(__name__)


class PatientService:
    """Service for managing patients."""

    def __init__(self, repo: PatientRepository) -> None:
        """Initialize the PatientService.

        Args:
            repo (PatientRepository): The patient repository.

        """
        self._repo = repo

    def find_or_create(self, request: PatientFindOrCreateRequest) -> PatientResponse:
        """Find an existing patient by email or create a new one.

        Args:
            request (PatientFindOrCreateRequest): The patient data.

        Returns:
            PatientResponse: The found or created patient.

        """
        existing = self._repo.find_by_email(request.email)
        if existing:
            logger.info("Found existing patient with email '%s'", request.email)
            return PatientResponse.from_entity(existing)

        patient = Patient(
            first_name=request.first_name,
            last_name=request.last_name,
            email=request.email,
            phone=request.phone,
            date_of_birth=request.date_of_birth,
            gender=request.gender,
        )
        created = self._repo.create(patient)
        logger.info("Created new patient with email '%s'", request.email)
        return PatientResponse.from_entity(created)

    def get_patient(self, patient_id: uuid.UUID) -> PatientResponse | None:
        """Get a patient by ID.

        Args:
            patient_id (uuid.UUID): The patient's ID.

        Returns:
            PatientResponse | None: The patient if found, else None.

        """
        patient = self._repo.get_by_id(patient_id)
        return PatientResponse.from_entity(patient) if patient else None

    def get_patient_by_email(self, email: str) -> PatientResponse | None:
        """Look up a patient by email.

        Args:
            email (str): The patient's email address.

        Returns:
            PatientResponse | None: The patient if found, else None.

        """
        patient = self._repo.get_by_email(email)
        return PatientResponse.from_entity(patient) if patient else None


class DoctorService:
    """Service for managing doctors."""

    def __init__(self, repo: DoctorRepository) -> None:
        """Initialize the DoctorService.

        Args:
            repo (DoctorRepository): The doctor repository.

        """
        self._repo = repo

    def get_doctor(self, doctor_id: uuid.UUID) -> DoctorResponse | None:
        """Get a doctor by ID.

        Args:
            doctor_id (uuid.UUID): The doctor's ID.

        Returns:
            DoctorResponse | None: The doctor if found, else None.

        """
        doctor = self._repo.get_by_id(doctor_id)
        return DoctorResponse.from_entity(doctor) if doctor else None

    def get_all_doctors(self) -> list[DoctorResponse]:
        """Get all doctors.

        Returns:
            list[DoctorResponse]: All doctors.

        """
        return [DoctorResponse.from_entity(d) for d in self._repo.get_all()]
