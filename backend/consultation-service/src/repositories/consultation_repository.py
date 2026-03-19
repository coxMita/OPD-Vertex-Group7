"""Repository for consultation data access."""

import uuid

from sqlmodel import Session, select

from src.models.db.consultation import Consultation, ConsultationStatus


class ConsultationRepository:
    """Repository for managing Consultation entities in the database."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session (Session): The database session.

        """
        self._session = session

    def create(self, consultation: Consultation) -> Consultation:
        """Create a new consultation in the database.

        Args:
            consultation (Consultation): The consultation entity to create.

        Returns:
            Consultation: The created consultation with updated fields.

        """
        self._save_and_refresh(consultation)
        return consultation

    def get_by_id(self, consultation_id: uuid.UUID) -> Consultation | None:
        """Retrieve a consultation by its ID.

        Args:
            consultation_id (uuid.UUID): The ID of the consultation.

        Returns:
            Consultation | None: The consultation if found, else None.

        """
        return self._session.get(Consultation, consultation_id)

    def get_by_appointment_id(self, appointment_id: uuid.UUID) -> Consultation | None:
        """Retrieve a consultation by its appointment ID.

        Args:
            appointment_id (uuid.UUID): The ID of the appointment.

        Returns:
            Consultation | None: The consultation if found, else None.

        """
        return self._session.exec(
            select(Consultation).where(Consultation.appointment_id == appointment_id)
        ).first()

    def get_by_doctor_id(self, doctor_id: uuid.UUID) -> list[Consultation]:
        """Retrieve all consultations for a specific doctor.

        Args:
            doctor_id (uuid.UUID): The ID of the doctor.

        Returns:
            list[Consultation]: List of the doctor's consultations.

        """
        return list(
            self._session.exec(
                select(Consultation).where(Consultation.doctor_id == doctor_id)
            )
        )

    def update(
        self,
        consultation: Consultation,
        **kwargs: str | ConsultationStatus | None,
    ) -> Consultation:
        """Update a consultation with the given fields.

        Args:
            consultation (Consultation): The consultation entity to update.
            **kwargs: Fields to update.

        Returns:
            Consultation: The updated consultation.

        """
        for key, value in kwargs.items():
            if value is not None:
                setattr(consultation, key, value)
        self._save_and_refresh(consultation)
        return consultation

    def update_status(
        self, consultation: Consultation, status: ConsultationStatus
    ) -> Consultation:
        """Update the status of a consultation.

        Args:
            consultation (Consultation): The consultation entity to update.
            status (ConsultationStatus): The new status.

        Returns:
            Consultation: The updated consultation.

        """
        consultation.status = status
        self._save_and_refresh(consultation)
        return consultation

    def _save_and_refresh(self, instance: Consultation) -> None:
        """Save and refresh an instance in the database.

        Args:
            instance (Consultation): The consultation instance to save and refresh.

        """
        self._session.add(instance)
        self._session.commit()
        self._session.refresh(instance)
