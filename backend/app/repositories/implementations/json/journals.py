from collections.abc import Callable
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from app.repositories.implementations.json.store import JsonStore
from app.repositories.journals import JournalStorageError
from app.schemas.journals import JournalDetailResponse


class JsonJournalRepository:
    def __init__(self, path: Path) -> None:
        self.store = JsonStore(path, TypeAdapter(list[JournalDetailResponse]))

    def read(self) -> list[JournalDetailResponse]:
        try:
            return self.store.read()
        except (OSError, UnicodeError, ValidationError) as exc:
            raise JournalStorageError("Unable to read journals.") from exc

    def change[T](self, action: Callable[[list[JournalDetailResponse]], T]) -> T:
        try:
            return self.store.update(action)
        except (OSError, UnicodeError, ValidationError) as exc:
            raise JournalStorageError("Unable to save journals.") from exc
