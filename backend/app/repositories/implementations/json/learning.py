from pathlib import Path
from uuid import UUID

from pydantic import TypeAdapter, ValidationError

from app.repositories.learning import LearningStorageError
from app.schemas.progress import StoredProgress
from app.schemas.vocabulary import DailyVocabularyItem


class JsonLearningRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def _read[T](self, filename: str, adapter: TypeAdapter[T]) -> T:
        try:
            return adapter.validate_json((self.data_dir / filename).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValidationError) as exc:
            raise LearningStorageError("Unable to load learning data.") from exc

    def get_progress(
        self, user_id: UUID, language_code: str | None = None
    ) -> StoredProgress | None:
        rows = self._read("progress.json", TypeAdapter(list[StoredProgress]))
        return next(
            (
                row
                for row in rows
                if row.user_id == user_id
                and (language_code is None or row.language_code.lower() == language_code)
            ),
            None,
        )

    def list_vocabulary(self, user_id: UUID) -> list[DailyVocabularyItem]:
        rows = self._read("vocabulary.json", TypeAdapter(list[DailyVocabularyItem]))
        for row in rows:
            if row.progress is None or row.progress.vocabulary_item_id != row.vocabulary.id:
                raise LearningStorageError("Invalid vocabulary progress reference.")
            if row.translation and row.translation.vocabulary_item_id != row.vocabulary.id:
                raise LearningStorageError("Invalid vocabulary translation reference.")
        return [row for row in rows if row.progress and row.progress.user_id == user_id]
