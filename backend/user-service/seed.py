"""Seed script — inserts initial doctors into the database.

Run once after migrations:
    uv run python seed.py

This script is for development only. When Keycloak is integrated,
doctors will be created via find-or-create on first login.
"""

import logging
import os
import uuid

from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select

from src.models.db.user import Doctor

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCTORS = [
    Doctor(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        first_name="Anders",
        last_name="Hansen",
        email="a.hansen@opd-vertex.dk",
        specialization="General Practice",
    ),
    Doctor(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        first_name="Maria",
        last_name="Nielsen",
        email="m.nielsen@opd-vertex.dk",
        specialization="Cardiology",
    ),
    Doctor(
        id=uuid.UUID("00000000-0000-0000-0000-000000000003"),
        first_name="Lars",
        last_name="Christensen",
        email="l.christensen@opd-vertex.dk",
        specialization="Neurology",
    ),
]


def seed() -> None:
    """Insert doctors into the database if they don't already exist."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set.")

    engine = create_engine(database_url)

    with Session(engine) as session:
        for doctor in DOCTORS:
            existing = session.exec(
                select(Doctor).where(Doctor.id == doctor.id)
            ).first()
            if existing:
                logger.info("Doctor %s already exists, skipping.", doctor.email)
                continue
            session.add(doctor)
            logger.info(
                "Inserted doctor: %s %s (%s)",
                doctor.first_name,
                doctor.last_name,
                doctor.specialization,
            )
        session.commit()

    logger.info("Seed complete.")


if __name__ == "__main__":
    seed()
