from collections.abc import Callable
from typing import Protocol

from app.schemas.progress import StoredProgress


class PracticeStorageError(Exception):
    pass


class PracticeRepository(Protocol):
    def read(self) -> list[StoredProgress]: ...

    def change[T](self, action: Callable[[list[StoredProgress]], T]) -> T: ...
