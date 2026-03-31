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

from src.models.db.doctor import Doctor

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCTORS = [
    Doctor(
        doctor_id=uuid.UUID("00000000-0000-0000-0001-000000000001"),
        full_name="Anders Hansen",
        department_name="General Practice",
        email="a.hansen@opd-vertex.dk",
        keycloak_id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
    ),
    Doctor(
        doctor_id=uuid.UUID("00000000-0000-0000-0001-000000000002"),
        full_name="Maria Nielsen",
        department_name="Cardiology",
        email="m.nielsen@opd-vertex.dk",
        keycloak_id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000002"),
    ),
    Doctor(
        doctor_id=uuid.UUID("00000000-0000-0000-0001-000000000003"),
        full_name="Lars Christensen",
        department_name="Neurology",
        email="l.christensen@opd-vertex.dk",
        keycloak_id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000003"),
    ),
    Doctor(
        doctor_id=uuid.UUID("00000000-0000-0000-0001-000000000004"),
        full_name="Sofie Pedersen",
        department_name="Orthopedics",
        email="s.pedersen@opd-vertex.dk",
        keycloak_id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000004"),
    ),
    Doctor(
        doctor_id=uuid.UUID("00000000-0000-0000-0001-000000000005"),
        full_name="Mikkel Andersen",
        department_name="Dermatology",
        email="m.andersen@opd-vertex.dk",
        keycloak_id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000005"),
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
                select(Doctor).where(Doctor.doctor_id == doctor.doctor_id)
            ).first()
            if existing:
                logger.info("Doctor %s already exists, skipping.", doctor.email)
                continue
            session.add(doctor)
            logger.info(
                "Inserted doctor: %s (%s)",
                doctor.full_name,
                doctor.department_name,
            )
        session.commit()

    logger.info("Seed complete.")


if __name__ == "__main__":
    seed()
