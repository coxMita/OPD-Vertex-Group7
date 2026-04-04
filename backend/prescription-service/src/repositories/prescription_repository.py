"""Repository for prescription data access."""

import uuid

from sqlmodel import Session, select

from src.models.db.prescription import Prescription, PrescriptionStatus


class PrescriptionRepository:
    """Repository for managing Prescription entities in the database."""

    def __init__(self, session: Session) -> None:
        """Initialise the repository with a database session.

        Args:
            session: The database session.

        """
        self._session = session

    def create(self, prescription: Prescription) -> Prescription:
        """Create a new prescription in the database.

        Args:
            prescription: The prescription entity to create.

        Returns:
            Prescription: The created prescription with updated fields.

        """
        self._save_and_refresh(prescription)
        return prescription

    def get_by_id(self, prescription_id: uuid.UUID) -> Prescription | None:
        """Retrieve a prescription by its ID.

        Args:
            prescription_id: The UUID of the prescription.

        Returns:
            Prescription | None: The prescription if found, else None.

        """
        return self._session.get(Prescription, prescription_id)

    def get_by_consultation_id(self, consultation_id: uuid.UUID) -> Prescription | None:
        """Retrieve the most recent prescription for a consultation.

        Args:
            consultation_id: The UUID of the consultation.

        Returns:
            Prescription | None: The prescription if found, else None.

        """
        return self._session.exec(
            select(Prescription)
            .where(Prescription.consultation_id == consultation_id)
            .order_by(Prescription.approved_at.desc().nullslast())
            .limit(1)
        ).first()

    def get_by_patient_id(self, patient_id: uuid.UUID) -> list[Prescription]:
        """Retrieve all prescriptions for a patient.

        Args:
            patient_id: The UUID of the patient.

        Returns:
            list[Prescription]: The patient's prescriptions.

        """
        return list(
            self._session.exec(
                select(Prescription).where(Prescription.patient_id == patient_id)
            )
        )

    def update_status(
        self, prescription: Prescription, status: PrescriptionStatus
    ) -> Prescription:
        """Update the status of a prescription.

        Args:
            prescription: The prescription entity to update.
            status: The new status.

        Returns:
            Prescription: The updated prescription.

        """
        prescription.status = status
        self._save_and_refresh(prescription)
        return prescription

    def _save_and_refresh(self, instance: Prescription) -> None:
        """Save and refresh an instance in the database.

        Args:
            instance: The prescription instance to save and refresh.

        """
        self._session.add(instance)
        self._session.commit()
        self._session.refresh(instance)
