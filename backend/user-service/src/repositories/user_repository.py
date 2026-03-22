"""Repository for user data access."""

import uuid

from sqlmodel import Session, select

from src.models.db.user import Doctor, Patient


class PatientRepository:
    """Repository for managing Patient entities."""

    def __init__(self, session: Session) -> None:
        """Initialize with a database session.

        Args:
            session (Session): The database session.

        """
        self._session = session

    def get_by_email(self, email: str) -> Patient | None:
        """Find a patient by email.

        Args:
            email (str): The patient's email.

        Returns:
            Patient | None: The patient if found, else None.

        """
        return self._session.exec(select(Patient).where(Patient.email == email)).first()

    def get_by_id(self, patient_id: uuid.UUID) -> Patient | None:
        """Get a patient by ID.

        Args:
            patient_id (uuid.UUID): The patient's ID.

        Returns:
            Patient | None: The patient if found, else None.

        """
        return self._session.get(Patient, patient_id)

    def create(self, patient: Patient) -> Patient:
        """Create a new patient.

        Args:
            patient (Patient): The patient entity to create.

        Returns:
            Patient: The created patient.

        """
        self._session.add(patient)
        self._session.commit()
        self._session.refresh(patient)
        return patient


class DoctorRepository:
    """Repository for managing Doctor entities."""

    def __init__(self, session: Session) -> None:
        """Initialize with a database session.

        Args:
            session (Session): The database session.

        """
        self._session = session

    def get_by_id(self, doctor_id: uuid.UUID) -> Doctor | None:
        """Get a doctor by ID.

        Args:
            doctor_id (uuid.UUID): The doctor's ID.

        Returns:
            Doctor | None: The doctor if found, else None.

        """
        return self._session.get(Doctor, doctor_id)

    def get_all(self) -> list[Doctor]:
        """Get all doctors.

        Returns:
            list[Doctor]: All doctors in the system.

        """
        return list(self._session.exec(select(Doctor)))

    def create(self, doctor: Doctor) -> Doctor:
        """Create a new doctor.

        Args:
            doctor (Doctor): The doctor entity to create.

        Returns:
            Doctor: The created doctor.

        """
        self._session.add(doctor)
        self._session.commit()
        self._session.refresh(doctor)
        return doctor
