from uuid import UUID

from sqlmodel import Session, select

from src.models.db.patient import Patient


class PatientRepository:
    """Repository for managing Patient entities in the database."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session."""
        self._session = session

    def create(self, patient: Patient) -> Patient:
        """Create a new patient in the database."""
        self._session.add(patient)
        self._session.commit()
        self._session.refresh(patient)
        return patient

    def get_by_id(self, patient_id: UUID) -> Patient | None:
        """Retrieve a patient by their ID."""
        return self._session.get(Patient, patient_id)

    def get_by_email(self, email: str) -> Patient | None:
        """Retrieve a patient by their email address."""
        return self._session.exec(select(Patient).where(Patient.email == email)).first()
