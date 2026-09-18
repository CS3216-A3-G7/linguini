"""Internal AI-run observability. No provider calls, raw prompts, or public endpoints."""

from uuid import UUID

from pydantic import ValidationError
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Engine,
    MetaData,
    String,
    Table,
    Text,
    Uuid,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.repositories.ai import AiRunConflictError, AiRunNotFoundError, AiRunStorageError
from app.schemas.ai import AiGenerationRun, AiGenerationRunCompletion
from app.schemas.base import utc_now
from app.schemas.enums import AiRunStatus

ai_generation_runs = Table(
    "ai_generation_runs",
    MetaData(),
    Column("id", Uuid, primary_key=True),
    Column("user_id", Uuid),
    Column("session_id", Uuid),
    Column("journal_id", Uuid),
    Column("feature", String(23), nullable=False),
    Column("model_name", Text, nullable=False),
    Column("prompt_version", Text, nullable=False),
    Column("schema_version", Text, nullable=False),
    Column("status", String(9), nullable=False),
    Column("latency_ms", BigInteger),
    Column("input_tokens", BigInteger),
    Column("output_tokens", BigInteger),
    Column("validation_passed", Boolean),
    Column("error_code", String(100)),
    Column("input_reference", Text),
    Column("output_reference", Text),
    Column("completed_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    schema="public",
)

IDENTITY_FIELDS = (
    "user_id",
    "session_id",
    "journal_id",
    "feature",
    "model_name",
    "prompt_version",
    "schema_version",
    "input_reference",
)


def same_identity(left: AiGenerationRun, right: AiGenerationRun) -> bool:
    return all(getattr(left, field) == getattr(right, field) for field in IDENTITY_FIELDS)


class PostgresAiGenerationRunRepository:
    def __init__(self, engine: Engine, user_id: UUID | None) -> None:
        self.engine = engine
        self.user_id = user_id

    def _scope(self):
        return ai_generation_runs.c.user_id == self.user_id

    def get(self, run_id: UUID) -> AiGenerationRun | None:
        try:
            with self.engine.connect() as connection:
                row = (
                    connection.execute(
                        select(ai_generation_runs).where(
                            self._scope(), ai_generation_runs.c.id == run_id
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                return AiGenerationRun.model_validate(dict(row)) if row is not None else None
        except (SQLAlchemyError, ValidationError) as exc:
            raise AiRunStorageError("Unable to load AI run.") from exc

    def list_runs(
        self, *, session_id: UUID | None = None, journal_id: UUID | None = None, limit: int = 100
    ) -> list[AiGenerationRun]:
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        statement = select(ai_generation_runs).where(self._scope())
        if session_id is not None:
            statement = statement.where(ai_generation_runs.c.session_id == session_id)
        if journal_id is not None:
            statement = statement.where(ai_generation_runs.c.journal_id == journal_id)
        try:
            with self.engine.connect() as connection:
                return [
                    AiGenerationRun.model_validate(dict(row))
                    for row in connection.execute(
                        statement.order_by(
                            ai_generation_runs.c.created_at.desc(), ai_generation_runs.c.id
                        ).limit(limit)
                    ).mappings()
                ]
        except (SQLAlchemyError, ValidationError) as exc:
            raise AiRunStorageError("Unable to load AI runs.") from exc

    def create(self, run: AiGenerationRun) -> AiGenerationRun:
        run = AiGenerationRun.model_validate(run.model_dump(by_alias=False))
        if run.user_id != self.user_id:
            raise AiRunConflictError("AI run belongs to another scope.")
        if run.status is not AiRunStatus.PENDING:
            raise AiRunConflictError(
                "Create pending runs; finish them separately or import history."
            )
        try:
            with self.engine.begin() as connection:
                row = (
                    connection.execute(
                        insert(ai_generation_runs)
                        .values(**run.model_dump(by_alias=False))
                        .on_conflict_do_nothing(index_elements=[ai_generation_runs.c.id])
                        .returning(ai_generation_runs)
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is not None:
                    return AiGenerationRun.model_validate(dict(row))
                row = (
                    connection.execute(
                        select(ai_generation_runs)
                        .where(self._scope(), ai_generation_runs.c.id == run.id)
                        .with_for_update()
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    raise AiRunConflictError("AI run ID is already in use.")
                stored = AiGenerationRun.model_validate(dict(row))
                if not same_identity(stored, run):
                    raise AiRunConflictError("AI run ID is already used for a different operation.")
                # A retried job can discover it already finished instead of calling the model again.
                return stored
        except IntegrityError as exc:
            raise AiRunConflictError("Invalid AI run ownership or references.") from exc
        except (SQLAlchemyError, ValidationError) as exc:
            raise AiRunStorageError("Unable to create AI run.") from exc

    def finish(self, run_id: UUID, result: AiGenerationRunCompletion) -> AiGenerationRun:
        result = AiGenerationRunCompletion.model_validate(
            result.model_dump(exclude_unset=True, by_alias=False)
        )
        changes = result.model_dump(exclude_unset=True, by_alias=False)
        if changes.get("completed_at") is None:
            changes.pop("completed_at", None)
        try:
            with self.engine.begin() as connection:
                row = (
                    connection.execute(
                        select(ai_generation_runs)
                        .where(self._scope(), ai_generation_runs.c.id == run_id)
                        .with_for_update()
                    )
                    .mappings()
                    .one_or_none()
                )
                if row is None:
                    raise AiRunNotFoundError("AI run not found.")
                stored = AiGenerationRun.model_validate(dict(row))
                if stored.status is not AiRunStatus.PENDING:
                    if any(getattr(stored, field) != value for field, value in changes.items()):
                        raise AiRunConflictError(
                            "AI run has already finished with a different result."
                        )
                    return stored
                changes.setdefault("completed_at", utc_now())
                # Validate the complete transition without transient invalid assignment states.
                AiGenerationRun.model_validate(stored.model_dump(by_alias=False) | changes)
                saved = (
                    connection.execute(
                        update(ai_generation_runs)
                        .where(ai_generation_runs.c.id == run_id)
                        .values(**changes)
                        .returning(ai_generation_runs)
                    )
                    .mappings()
                    .one()
                )
                return AiGenerationRun.model_validate(dict(saved))
        except IntegrityError as exc:
            raise AiRunConflictError("Invalid AI run transition.") from exc
        except (SQLAlchemyError, ValidationError) as exc:
            raise AiRunStorageError("Unable to finish AI run.") from exc
