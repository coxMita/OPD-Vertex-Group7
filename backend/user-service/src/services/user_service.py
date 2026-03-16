import asyncio
import logging

from src.messaging.messaging_manager import MessagingManager
from src.messaging.pubsub_exchanges import USER_CREATED
from src.models.db.user import User
from src.models.dto.user_create_request import UserCreateRequest
from src.models.dto.user_dto import UserDTO
from src.models.dto.user_update_request import UserUpdateRequest
from src.models.msg.abstract_message import AbstractMessage
from src.models.msg.user_message import UserMessage
from src.repositories.user_repository import UserRepository


logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users."""

    def __init__(self, repo: UserRepository, messaging: MessagingManager) -> None:
        """Initialize the UserService."""
        self._repo = repo
        self._messaging = messaging

    def create_user(self, request: UserCreateRequest) -> UserDTO:
        """Create a new user if it doesn't exist."""
        existing_user = self._repo.get_by_id(request.user_id)
        if existing_user is not None:
            raise ValueError("User already exists")

        user = User(
            user_id=request.user_id,
        )
        created = self._repo.create(user)
        dto = UserDTO(
            user_id=str(created.user_id),
        )
        self._publish(UserMessage.from_entity(created), USER_CREATED)
        return dto

    def get_user(self, user_id: str) -> UserDTO | None:
        """Get a user by user_id."""
        user = self._repo.get_by_id(user_id)
        return (
            UserDTO(
                user_id=str(user.user_id),
            )
            if user
            else None
        )

    def update_preferences(
        self, user_id: str, request: UserUpdateRequest
    ) -> UserDTO | None:
        """Update user preferences."""
        user = self._repo.get_by_id(user_id)
        if user is None:
            user = self._repo.create(User(user_id=user_id))

        updated = self._repo.update(user)
        return UserDTO(
            user_id=str(updated.user_id),
        )

    def list_users(self) -> list[UserDTO]:
        """List all users."""
        users = self._repo.get_all()
        return [
            UserDTO(
                user_id=str(user.user_id),
            )
            for user in users
        ]

    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        return self._repo.delete(user_id)

    def _publish(self, message: AbstractMessage, exchange: str) -> None:
        """Publish a message asynchronously.

        This method schedules the publish operation on the event loop and logs
        any errors that happen in the background task.
        """
        try:
            task = asyncio.create_task(
                self._messaging.get_pubsub(exchange).publish(message)
            )
            task.add_done_callback(UserService._log_task_exception)
        except RuntimeError:
            logger.exception("Failed to publish event to exchange '%s'", exchange)

    @staticmethod
    def _log_task_exception(task: asyncio.Task) -> None:
        """Log exceptions raised in background publish tasks."""
        try:
            task.result()
        except Exception as e:
            logger.exception("Background publish failed: %s", e)
