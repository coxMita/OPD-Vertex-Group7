from typing import Optional
from uuid import UUID

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """User database model storing only Keycloak user_id."""

    # Keycloak user_id as primary key
    user_id: UUID = Field(primary_key=True, index=True, nullable=False, unique=True)
