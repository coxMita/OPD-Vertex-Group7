from pydantic import BaseModel


class AbstractMessage(BaseModel):
    """Abstract base class for messages to be sent and received via messaging system."""

    def to_bytes(self) -> bytes:
        """Serialize the message to bytes using JSON encoding.

        Returns:
            bytes: The serialized message in bytes.

        """
        return self.model_dump_json().encode()

    @classmethod
    def from_bytes(cls, body: bytes) -> "AbstractMessage":
        """Deserialize bytes to an instance of the message class.

        Args:
            body (bytes): The byte representation of the message.

        Returns:
            An instance of the message class.

        """
        return cls.model_validate_json(body)

    def __str__(self) -> str:
        """Return string representation of the message."""
        return f"{self.__class__.__name__}({self.model_dump()})"
