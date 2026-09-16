from collections.abc import Callable
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from app.repositories.implementations.json.store import JsonStore
from app.repositories.practice import PracticeStorageError
from app.schemas.progress import StoredProgress


class JsonPracticeRepository:
    def __init__(self, path: Path) -> None:
        self.store = JsonStore(path, TypeAdapter(list[StoredProgress]))

    def read(self) -> list[StoredProgress]:
        try:
            return self.store.read()
        except (OSError, UnicodeError, ValidationError) as exc:
            raise PracticeStorageError("Unable to load practice.") from exc

    def change[T](self, action: Callable[[list[StoredProgress]], T]) -> T:
        try:
            return self.store.update(action)
        except (OSError, UnicodeError, ValidationError) as exc:
            raise PracticeStorageError("Unable to save practice.") from exc
