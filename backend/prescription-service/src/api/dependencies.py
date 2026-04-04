"""Dependency injection for prescription-service."""

import logging
import os
from typing import Generator

from dotenv import load_dotenv
from fastapi import Depends
from sqlmodel import Session, create_engine

from src.repositories.prescription_repository import PrescriptionRepository
from src.services.prescription_service import PrescriptionService

logger = logging.getLogger(__name__)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL is not set. Please set it in the environment variables.")
    raise ValueError("DATABASE_URL is not set.")

engine = create_engine(DATABASE_URL, echo=True)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session.

    Yields:
        Session: A SQLModel database session.

    """
    with Session(engine) as session:
        yield session


def get_prescription_repository(
    session: Session = Depends(get_db_session),
) -> PrescriptionRepository:
    """Dependency injection for PrescriptionRepository.

    Args:
        session: The database session.

    Returns:
        PrescriptionRepository: An instance of PrescriptionRepository.

    """
    return PrescriptionRepository(session)


def get_prescription_service(
    repo: PrescriptionRepository = Depends(get_prescription_repository),
) -> PrescriptionService:
    """Dependency injection for PrescriptionService.

    Args:
        repo: The prescription repository.

    Returns:
        PrescriptionService: An instance of PrescriptionService.

    """
    return PrescriptionService(repo)
