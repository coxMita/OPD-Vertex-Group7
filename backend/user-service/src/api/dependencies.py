import logging
import os
from typing import Generator

from dotenv import load_dotenv
from fastapi.params import Depends
from sqlmodel import Session, create_engine

from src.repositories.doctor_repository import DoctorRepository
from src.repositories.patient_repository import PatientRepository
from src.services.doctor_service import DoctorService
from src.services.patient_service import PatientService

logger = logging.getLogger(__name__)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL is not set.")
    raise ValueError("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL, echo=True)


def get_db_session() -> Generator[Session, None, None]:
    """Dependency injection for database session."""
    with Session(engine) as session:
        yield session


def get_patient_repository(
    session: Session = Depends(get_db_session),
) -> PatientRepository:
    """Dependency injection for PatientRepository."""
    return PatientRepository(session)


def get_patient_service(
    repo: PatientRepository = Depends(get_patient_repository),
) -> PatientService:
    """Dependency injection for PatientService."""
    return PatientService(repo)


def get_doctor_repository(
    session: Session = Depends(get_db_session),
) -> DoctorRepository:
    """Dependency injection for DoctorRepository."""
    return DoctorRepository(session)


def get_doctor_service(
    repo: DoctorRepository = Depends(get_doctor_repository),
) -> DoctorService:
    """Dependency injection for DoctorService."""
    return DoctorService(repo)
