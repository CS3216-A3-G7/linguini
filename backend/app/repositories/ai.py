from typing import Protocol
from uuid import UUID

from app.schemas.ai import AiGenerationRun, AiGenerationRunCompletion


class AiRunStorageError(Exception):
    pass


class AiRunConflictError(Exception):
    pass


class AiRunNotFoundError(Exception):
    pass


class AiGenerationRunRepository(Protocol):
    """Internal repository scoped to one owner (None means system runs only)."""

    def create(self, run: AiGenerationRun) -> AiGenerationRun: ...
    def get(self, run_id: UUID) -> AiGenerationRun | None: ...
    def list_runs(
        self, *, session_id: UUID | None = None, journal_id: UUID | None = None, limit: int = 100
    ) -> list[AiGenerationRun]: ...
    def finish(self, run_id: UUID, result: AiGenerationRunCompletion) -> AiGenerationRun: ...
