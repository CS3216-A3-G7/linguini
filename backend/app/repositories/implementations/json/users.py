"""Read demo users from a JSON array using the existing User contract."""

from pathlib import Path
from uuid import UUID

from pydantic import TypeAdapter, ValidationError

from app.repositories.implementations.json.store import JsonStore
from app.repositories.users import UserRepositoryError
from app.schemas.base import utc_now
from app.schemas.users import UpdateUserRequest, User


class JsonUserRepository:
    def __init__(self, path: Path) -> None:
        self.path = path

    def get_by_id(self, user_id: UUID) -> User | None:
        try:
            users = TypeAdapter(list[User]).validate_json(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValidationError) as exc:
            raise UserRepositoryError("Unable to load demo users.") from exc
        return next((user for user in users if user.id == user_id), None)

    def update(self, user_id: UUID, request: UpdateUserRequest) -> User | None:
        def change(users: list[User]) -> User | None:
            for index, user in enumerate(users):
                if user.id == user_id:
                    values = user.model_dump(by_alias=False)
                    values.update(
                        request.model_dump(exclude_unset=True, exclude_none=True, by_alias=False)
                    )
                    values["updated_at"] = utc_now()
                    users[index] = User.model_validate(values)
                    return users[index]
            return None

        try:
            return JsonStore(self.path, TypeAdapter(list[User])).update(change)
        except (OSError, UnicodeError, ValidationError) as exc:
            raise UserRepositoryError("Unable to save demo user.") from exc
