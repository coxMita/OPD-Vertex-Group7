"""Dependency injection for user-service."""

import logging
import os
from typing import Generator

from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import Session, create_engine

from src.repositories.user_repository import DoctorRepository, PatientRepository
from src.services.user_service import DoctorService, PatientService

logger = logging.getLogger(__name__)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL, echo=True)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session.

    Yields:
        Session: A SQLModel database session.

    """
    with Session(engine) as session:
        yield session


def get_patient_repository(
    session: Session = Depends(get_db_session),
) -> PatientRepository:
    """Dependency injection for PatientRepository.

    Args:
        session (Session): The database session.

    Returns:
        PatientRepository: An instance of PatientRepository.

    """
    return PatientRepository(session)


def get_doctor_repository(
    session: Session = Depends(get_db_session),
) -> DoctorRepository:
    """Dependency injection for DoctorRepository.

    Args:
        session (Session): The database session.

    Returns:
        DoctorRepository: An instance of DoctorRepository.

    """
    return DoctorRepository(session)


def get_patient_service(
    repo: PatientRepository = Depends(get_patient_repository),
) -> PatientService:
    """Dependency injection for PatientService.

    Args:
        repo (PatientRepository): The patient repository.

    Returns:
        PatientService: An instance of PatientService.

    """
    return PatientService(repo)


def get_doctor_service(
    repo: DoctorRepository = Depends(get_doctor_repository),
) -> DoctorService:
    """Dependency injection for DoctorService.

    Args:
        repo (DoctorRepository): The doctor repository.

    Returns:
        DoctorService: An instance of DoctorService.

    """
    return DoctorService(repo)
