"""Abstract base class for messages."""

from pydantic import BaseModel


class AbstractMessage(BaseModel):
    """Abstract base class for messages to be sent and received via messaging system."""

    def to_bytes(self) -> bytes:
        """Serialise the message to bytes using JSON encoding."""
        return self.model_dump_json().encode()

    @classmethod
    def from_bytes(cls, body: bytes) -> "AbstractMessage":
        """Deserialise bytes to an instance of the message class."""
        return cls.model_validate_json(body)

    def __str__(self) -> str:
        """Return string representation of the message."""
        return f"{self.__class__.__name__}({self.model_dump()})"
