"""Import a trusted {tasks: [], attempts: [], hints: []} bundle in one transaction."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, model_validator
from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert

from app.database import create_database_engine
from app.repositories.implementations.postgres.practice import sessions
from app.repositories.implementations.postgres.tasks import (
    entity_values,
    session_tasks,
    task_attempts,
    task_hints,
)
from app.repositories.implementations.postgres.users import users
from app.schemas.base import ApiModel
from app.schemas.tasks import SessionTask, TaskAttempt, TaskHint


class TaskImportBundle(ApiModel):
    tasks: list[SessionTask] = Field(default_factory=list)
    attempts: list[TaskAttempt] = Field(default_factory=list)
    hints: list[TaskHint] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_records(self):
        for records, fields in (
            (self.tasks, ("session_id", "order_index")),
            (self.attempts, ("session_task_id", "attempt_number")),
            (self.hints, ("session_task_id", "hint_level")),
        ):
            if len({record.id for record in records}) != len(records):
                raise ValueError("Duplicate entity IDs in import.")
            if len(
                {tuple(getattr(record, field) for field in fields) for record in records}
            ) != len(records):
                raise ValueError("Duplicate task positions, attempt numbers or hint levels.")
        return self


def import_tasks(engine: Engine, path: Path) -> dict[str, int]:
    bundle = TaskImportBundle.model_validate_json(path.read_text(encoding="utf-8"))
    groups = [
        (session_tasks, bundle.tasks, "session_id"),
        (task_attempts, bundle.attempts, "session_task_id"),
        (task_hints, bundle.hints, "session_task_id"),
    ]
    counts = {table.name: 0 for table, _, _ in groups}
    # Serialize with session/practice writers. Historical terminal records are allowed here.
    with engine.begin() as connection:
        task_ids = {record.session_task_id for record in [*bundle.attempts, *bundle.hints]}
        session_ids = {task.session_id for task in bundle.tasks}
        session_ids.update(
            connection.execute(
                select(session_tasks.c.session_id).where(session_tasks.c.id.in_(task_ids))
            ).scalars()
        )
        owners = (
            connection.execute(select(sessions.c.user_id).where(sessions.c.id.in_(session_ids)))
            .scalars()
            .all()
        )
        for owner in sorted(set(owners), key=str):
            connection.execute(select(users.c.id).where(users.c.id == owner).with_for_update())
        for table, records, parent in groups:
            for record in records:
                existing = connection.execute(
                    select(table.c[parent]).where(table.c.id == record.id)
                ).scalar_one_or_none()
                if existing is not None:
                    if existing != getattr(record, parent):
                        raise ValueError("Existing ID belongs to a different parent.")
                    continue
                connection.execute(insert(table).values(**entity_values(record)))
                counts[table.name] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, type=Path)
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
    engine = create_database_engine()
    try:
        counts = import_tasks(engine, args.path)
    except Exception:
        raise SystemExit(
            "Task import failed. Check the bundle, migrations, parent sessions, "
            "scene objects, vocabulary and owned audio references."
        ) from None
    finally:
        engine.dispose()
    print(f"Imported {counts}. Existing IDs were left unchanged.")


if __name__ == "__main__":
    main()
