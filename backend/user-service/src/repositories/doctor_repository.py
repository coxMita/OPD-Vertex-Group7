from uuid import UUID

from sqlmodel import Session, select

from src.models.db.doctor import Doctor


class DoctorRepository:
    """Repository for managing Doctor entities in the database."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session."""
        self._session = session

    def get_by_id(self, doctor_id: UUID) -> Doctor | None:
        """Retrieve a doctor by their ID."""
        return self._session.get(Doctor, doctor_id)

    def get_all_by_department(self, department_name: str) -> list[Doctor]:
        """Retrieve all doctors in a specific department."""
        statement = select(Doctor).where(Doctor.department_name == department_name)
        return list(self._session.exec(statement).all())

    def get_by_keycloak_id(self, keycloak_id: UUID) -> Doctor | None:
        """Retrieve a doctor by their Keycloak ID."""
        return self._session.exec(
            select(Doctor).where(Doctor.keycloak_id == keycloak_id)
        ).first()
