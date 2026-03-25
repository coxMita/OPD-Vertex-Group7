from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Doctor(SQLModel, table=True):
    """Doctor database model."""

    doctor_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
        unique=True,
    )
    full_name: str = Field(nullable=False)
    department_name: str = Field(nullable=False)
    email: str = Field(nullable=False)
    keycloak_id: UUID = Field(nullable=False, unique=True)
