import logging
import os
from typing import Generator

from dotenv import load_dotenv
from fastapi.params import Depends
from sqlmodel import Session, create_engine

from src.messaging.messaging_manager import MessagingManager, messaging_manager
from src.repositories.patient_repository import PatientRepository
from src.repositories.doctor_repository import DoctorRepository
from src.repositories.user_repository import UserRepository
from src.services.patient_service import PatientService
from src.services.doctor_service import DoctorService
from src.services.user_service import UserService

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


def get_user_repository(
    session: Session = Depends(get_db_session),
) -> UserRepository:
    """Dependency injection for UserRepository."""
    return UserRepository(session)


def get_user_service(
    repo: UserRepository = Depends(get_user_repository),
    messaging: MessagingManager = Depends(lambda: messaging_manager),
) -> UserService:
    """Dependency injection for UserService."""
    return UserService(repo, messaging)


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
