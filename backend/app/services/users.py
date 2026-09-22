"""Current demo-user lookup, independent of HTTP and storage format."""

from uuid import UUID

from app.repositories.users import UserRepository
from app.schemas.users import UpdateUserRequest, User


class UserNotFoundError(Exception):
    """The configured demo user does not exist."""


class UserService:
    def __init__(self, repository: UserRepository, demo_user_id: UUID) -> None:
        self.repository = repository
        self.demo_user_id = demo_user_id
        self._current_user: User | None = None

    def get_current_user(self) -> User:
        if self._current_user is None:
            user = self.repository.get_by_id(self.demo_user_id)
            if user is None:
                raise UserNotFoundError("The configured demo user was not found.")
            self._current_user = user
        return self._current_user

    def update_current_user(self, request: UpdateUserRequest) -> User:
        user = self.repository.update(self.demo_user_id, request)
        if user is None:
            raise UserNotFoundError("The configured demo user was not found.")
        self._current_user = user
        return user
