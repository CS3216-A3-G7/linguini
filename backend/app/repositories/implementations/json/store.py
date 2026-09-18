"""Atomic JSON updates for the single-process demo backend."""

import os
from collections.abc import Callable
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock

from pydantic import TypeAdapter

_lock = RLock()


class JsonStore[T]:
    def __init__(self, path: Path, adapter: TypeAdapter[T]) -> None:
        self.path = path
        self.adapter = adapter

    def read(self) -> T:
        # Windows cannot replace an open file; serialize reads with atomic writes.
        with _lock:
            return self.adapter.validate_json(self.path.read_text(encoding="utf-8"))

    def update[R](self, change: Callable[[T], R]) -> R:
        with _lock:
            data = self.read()
            result = change(data)
            payload = self.adapter.dump_json(data, by_alias=True, indent=2)
            temporary = None
            try:
                with NamedTemporaryFile(dir=self.path.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(payload + b"\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, self.path)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            return result
