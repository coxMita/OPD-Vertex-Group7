"""User event message."""

from src.models.db.user import User
from src.models.msg.abstract_message import AbstractMessage


class UserMessage(AbstractMessage):
    """Message published when a user event occurs."""

    user_id: str

    @classmethod
    def from_entity(cls, entity: User) -> "UserMessage":
        """Create a UserMessage from a User entity."""
        return cls(
            user_id=str(entity.user_id),
        )
