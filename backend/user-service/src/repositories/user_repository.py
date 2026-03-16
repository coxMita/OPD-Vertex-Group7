from sqlmodel import Session, select

from src.models.db.user import User


class UserRepository:
    """Repository for managing User entities in the database."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session."""
        self._session = session

    def create(self, user: User) -> User:
        """Create a new user in the database."""
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def get_by_id(self, user_id: str) -> User | None:
        """Retrieve a user by their Keycloak user_id."""
        return self._session.get(User, user_id)

    def get_all(self) -> list[User]:
        """Retrieve all users."""
        statement = select(User)
        return list(self._session.exec(statement).all())

    def update(self, user: User) -> User:
        """Update an existing user."""
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        return user

    def delete(self, user_id: str) -> bool:
        """Delete a user by user_id."""
        user = self._session.get(User, user_id)
        if not user:
            return False
        self._session.delete(user)
        self._session.commit()
        return True
