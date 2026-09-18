"""Relational sessions and atomic demo session/XP transactions, scoped to one user."""

from collections.abc import Callable
from uuid import UUID

from pydantic import TypeAdapter, ValidationError
from sqlalchemy import (
    Column,
    Connection,
    DateTime,
    Engine,
    Integer,
    MetaData,
    String,
    Table,
    Uuid,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.implementations.postgres.language_profiles import language_profiles
from app.repositories.implementations.postgres.users import users
from app.repositories.learning import LearningRepository
from app.repositories.practice import PracticeStorageError
from app.schemas.progress import StoredProgress
from app.schemas.sessions import Session, StoredDemoSession

sessions = Table(
    "sessions",
    MetaData(),
    Column("id", Uuid, primary_key=True),
    Column("user_id", Uuid, nullable=False),
    Column("language_profile_id", Uuid, nullable=False),
    Column("scene_media_asset_id", Uuid, nullable=False),
    Column("status", String(20), nullable=False),
    Column("started_at", DateTime(timezone=True)),
    Column("completed_at", DateTime(timezone=True)),
    Column("abandoned_at", DateTime(timezone=True)),
    Column("plan_version", String(100)),
    Column("failure_code", String(100)),
    Column("idempotency_key", String(200)),
    Column("demo_state", JSONB, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    schema="public",
)
practice_progress = Table(
    "user_practice_progress",
    MetaData(),
    Column("user_id", Uuid, primary_key=True),
    Column("language_code", String(35), primary_key=True),
    Column("xp", Integer, nullable=False),
    Column("scenarios", JSONB, nullable=False),
    Column("leaderboard", JSONB, nullable=False),
    schema="public",
)


def session_values(run: StoredDemoSession) -> dict:
    return run.session.model_dump(by_alias=False) | {
        "idempotency_key": run.idempotency_key,
        "demo_state": run.state.model_dump(mode="json", by_alias=False),
    }


def progress_values(row: StoredProgress) -> dict:
    return {
        "user_id": row.user_id,
        "language_code": row.language_code.lower(),
        "xp": row.xp,
        "scenarios": [value.model_dump(mode="json") for value in row.scenarios],
        "leaderboard": [value.model_dump(mode="json") for value in row.leaderboard],
    }


class PostgresPracticeRepository:
    def __init__(self, engine: Engine, user_id: UUID) -> None:
        self.engine = engine
        self.user_id = user_id

    def _read(self, connection: Connection) -> list[StoredProgress]:
        rows = {
            row["language_code"]: StoredProgress.model_validate(dict(row))
            for row in connection.execute(
                select(practice_progress)
                .where(practice_progress.c.user_id == self.user_id)
                .order_by(practice_progress.c.language_code)
            ).mappings()
        }
        for row in connection.execute(
            select(sessions, language_profiles.c.target_language_code)
            .join(language_profiles, sessions.c.language_profile_id == language_profiles.c.id)
            .where(sessions.c.user_id == self.user_id)
            .order_by(sessions.c.created_at, sessions.c.id)
        ).mappings():
            language = row["target_language_code"].lower()
            if language not in rows:
                raise PracticeStorageError("Session has no practice progress snapshot.")
            rows[language].practice_sessions.append(
                StoredDemoSession(
                    session=Session.model_validate({key: row[key] for key in Session.model_fields}),
                    state=row["demo_state"],
                    idempotency_key=row["idempotency_key"],
                )
            )
        return list(rows.values())

    def read(self) -> list[StoredProgress]:
        try:
            with self.engine.connect().execution_options(
                isolation_level="REPEATABLE READ"
            ) as connection:
                return self._read(connection)
        except (SQLAlchemyError, ValidationError) as exc:
            raise PracticeStorageError("Unable to load practice.") from exc

    def change[T](self, action: Callable[[list[StoredProgress]], T]) -> T:
        try:
            with self.engine.begin() as connection:
                if (
                    connection.execute(
                        select(users.c.id).where(users.c.id == self.user_id).with_for_update()
                    ).scalar_one_or_none()
                    is None
                ):
                    raise PracticeStorageError("Practice user does not exist.")
                rows = self._read(connection)
                before_rows = {row.language_code: progress_values(row) for row in rows}
                before_sessions = {
                    run.session.id: session_values(run)
                    for row in rows
                    for run in row.practice_sessions
                }
                result = action(rows)
                TypeAdapter(list[StoredProgress]).validate_python(
                    [row.model_dump() for row in rows]
                )
                languages = [row.language_code.lower() for row in rows]
                if len(set(languages)) != len(languages) or set(before_rows) - set(languages):
                    raise PracticeStorageError("Duplicate or removed progress snapshots.")
                profiles = {
                    row.id: row.target_language_code.lower()
                    for row in connection.execute(
                        select(
                            language_profiles.c.id, language_profiles.c.target_language_code
                        ).where(language_profiles.c.user_id == self.user_id)
                    )
                }
                for row in rows:
                    if any(
                        profiles.get(run.session.language_profile_id) != row.language_code.lower()
                        for run in row.practice_sessions
                    ):
                        raise PracticeStorageError(
                            "Session language does not match its progress snapshot."
                        )
                runs = [run for row in rows for run in row.practice_sessions]
                if set(before_sessions) - {run.session.id for run in runs}:
                    raise PracticeStorageError(
                        "Session removal requires an explicit deletion workflow."
                    )
                if len({run.session.id for run in runs}) != len(runs):
                    raise PracticeStorageError("Duplicate session IDs.")
                for row in rows:
                    if row.user_id != self.user_id:
                        raise PracticeStorageError("Invalid practice owner.")
                    values = progress_values(row)
                    if before_rows.get(row.language_code) != values:
                        statement = insert(practice_progress).values(**values)
                        connection.execute(
                            statement.on_conflict_do_update(
                                index_elements=["user_id", "language_code"],
                                set_={
                                    key: values[key] for key in ("xp", "scenarios", "leaderboard")
                                },
                            )
                        )
                # Abandon previous sessions before inserting a new in-progress session.
                for run in sorted(runs, key=lambda item: item.session.id not in before_sessions):
                    values = session_values(run)
                    before = before_sessions.get(run.session.id)
                    if before == values:
                        continue
                    if run.session.user_id != self.user_id:
                        raise PracticeStorageError("Invalid session owner.")
                    if before is not None:
                        if any(
                            before[key] != values[key]
                            for key in (
                                "user_id",
                                "language_profile_id",
                                "scene_media_asset_id",
                                "created_at",
                                "idempotency_key",
                            )
                        ):
                            raise PracticeStorageError("Session identity cannot be changed.")
                        statement = (
                            update(sessions).where(sessions.c.id == run.session.id).values(**values)
                        )
                    else:
                        statement = insert(sessions).values(**values)
                    saved = connection.execute(
                        statement.returning(sessions.c.updated_at)
                    ).scalar_one()
                    run.session.updated_at = saved
                return result
        except (SQLAlchemyError, ValidationError) as exc:
            raise PracticeStorageError("Unable to save practice.") from exc


class SessionBackedLearningRepository:
    def __init__(
        self, practice: PostgresPracticeRepository, vocabulary: LearningRepository
    ) -> None:
        self.practice = practice
        self.vocabulary = vocabulary

    def get_progress(
        self, user_id: UUID, language_code: str | None = None
    ) -> StoredProgress | None:
        if user_id != self.practice.user_id:
            return None
        return next(
            (
                row
                for row in self.practice.read()
                if language_code is None or row.language_code == language_code.lower()
            ),
            StoredProgress(
                user_id=user_id,
                language_code=language_code or "es",
                xp=0,
                scenarios=[],
                leaderboard=[],
            ),
        )

    def list_vocabulary(self, user_id: UUID):
        return self.vocabulary.list_vocabulary(user_id)
