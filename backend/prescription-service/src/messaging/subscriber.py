"""RabbitMQ subscriber callbacks for prescription-service."""

import asyncio
import logging

from src.api.dependencies import engine
from src.models.db.prescription import Prescription, PrescriptionStatus
from src.models.msg.ai_completed_message import AICompletedMessage
from src.repositories.prescription_repository import PrescriptionRepository

logger = logging.getLogger(__name__)


async def on_ai_completed_message(message: AICompletedMessage) -> None:
    """Handle an AICompletedMessage from the ai.completed exchange.

    Runs the DB write in a thread pool via asyncio.to_thread so the async
    event loop is never blocked — identical pattern to how appointment-service
    uses sync SQLModel from async APScheduler jobs.

    Args:
        message: The deserialised AICompletedMessage.

    """
    logger.info(
        (
            "Received ai.completed for consultation '%s' "
            "(file: '%s'). Saving prescription draft..."
        ),
        message.consultation_id,
        message.filename,
    )

    def _save() -> None:
        """Run inside a thread — safe to use sync Session here."""
        from sqlmodel import Session  # noqa: PLC0415

        with Session(engine) as session:
            repo = PrescriptionRepository(session)

            # Idempotency guard: skip if a prescription for this consultation exists
            existing = repo.get_by_consultation_id(message.consultation_id)
            if existing is not None:
                logger.info(
                    "Prescription already exists for consultation '%s'; skipping.",
                    message.consultation_id,
                )
                return

            import uuid  # noqa: PLC0415

            prescription = Prescription(
                consultation_id=message.consultation_id,
                # patient_id / doctor_id unknown at this stage — nil UUID placeholder
                patient_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                doctor_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                status=PrescriptionStatus.DRAFT,
                prescription_json=message.prescription,
                summary_json={"summary": message.summary},
            )
            repo.create(prescription)
            logger.info(
                "Prescription '%s' saved for consultation '%s'.",
                prescription.id,
                message.consultation_id,
            )

    try:
        await asyncio.to_thread(_save)
    except Exception:
        logger.exception(
            "Failed to persist prescription for consultation '%s'.",
            message.consultation_id,
        )
