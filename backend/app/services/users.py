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

    def get_current_user(self) -> User:
        user = self.repository.get_by_id(self.demo_user_id)
        if user is None:
            raise UserNotFoundError("The configured demo user was not found.")
        return user

    def update_current_user(self, request: UpdateUserRequest) -> User:
        user = self.repository.update(self.demo_user_id, request)
        if user is None:
            raise UserNotFoundError("The configured demo user was not found.")
        return user
