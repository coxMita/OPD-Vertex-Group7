from typing import Optional

from pydantic import BaseModel


class UserCreateRequest(BaseModel):
    """Request model for creating a user."""

    user_id: str
