from typing import Optional

from pydantic import BaseModel


class UserDTO(BaseModel):
    """Response model for user data."""

    user_id: str
