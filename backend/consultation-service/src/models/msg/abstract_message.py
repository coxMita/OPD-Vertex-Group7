"""Abstract message for events."""

from pydantic import BaseModel


class AbstractMessage(BaseModel):
    """Base class for all message types."""

    pass
