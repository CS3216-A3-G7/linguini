from collections.abc import Callable
from typing import Protocol

from app.schemas.journals import JournalDetailResponse


class JournalStorageError(Exception):
    pass


class JournalRepository(Protocol):
    def read(self) -> list[JournalDetailResponse]: ...

    def change[T](self, action: Callable[[list[JournalDetailResponse]], T]) -> T: ...
