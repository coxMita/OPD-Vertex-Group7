"""Abstract message for events."""

from pydantic import BaseModel


class AbstractMessage(BaseModel):
    """Base class for all message types."""

    def to_bytes(self) -> bytes:
        """Serialize message to bytes using JSON encoding."""
        return self.model_dump_json().encode()

    @classmethod
    def from_bytes(cls, body: bytes) -> "AbstractMessage":
        """Deserialize bytes to an instance of the message class."""
        return cls.model_validate_json(body)

    def __str__(self) -> str:
        """Return string representation of the message."""
        return f"{self.__class__.__name__}({self.model_dump()})"
