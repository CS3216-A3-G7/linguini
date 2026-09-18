"""Import practice snapshots and sessions atomically, optionally with scene objects."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from pydantic import TypeAdapter
from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert

from app.config import DEMO_USERS_PATH
from app.database import create_database_engine
from app.repositories.implementations.postgres.language_profiles import language_profiles
from app.repositories.implementations.postgres.practice import (
    practice_progress,
    progress_values,
    session_values,
    sessions,
)
from app.repositories.implementations.postgres.scene_objects import object_values, scene_objects
from app.repositories.implementations.postgres.users import users
from app.schemas.media import SceneObject
from app.schemas.progress import StoredProgress


def import_sessions(engine: Engine, path: Path, objects_path: Path | None = None) -> dict[str, int]:
    rows = TypeAdapter(list[StoredProgress]).validate_json(path.read_text(encoding="utf-8"))
    objects = (
        TypeAdapter(list[SceneObject]).validate_json(objects_path.read_text(encoding="utf-8"))
        if objects_path
        else []
    )
    keys = [(row.user_id, row.language_code.lower()) for row in rows]
    ids = [run.session.id for row in rows for run in row.practice_sessions]
    if (
        len(set(keys)) != len(keys)
        or len(set(ids)) != len(ids)
        or len({item.id for item in objects}) != len(objects)
    ):
        raise ValueError("Duplicate progress, session or scene object identities.")
    counts = {"progress": 0, "sessions": 0, "scene_objects": 0}
    with engine.begin() as connection:
        for owner in sorted({row.user_id for row in rows}, key=str):
            if (
                connection.execute(
                    select(users.c.id).where(users.c.id == owner).with_for_update()
                ).scalar_one_or_none()
                is None
            ):
                raise ValueError("Import users first.")
        for row in rows:
            for run in row.practice_sessions:
                profile = (
                    connection.execute(
                        select(language_profiles).where(
                            language_profiles.c.id == run.session.language_profile_id
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if (
                    profile is None
                    or profile["user_id"] != row.user_id
                    or run.session.user_id != row.user_id
                    or profile["target_language_code"].lower() != row.language_code.lower()
                ):
                    raise ValueError("Session must match its snapshot owner and profile language.")
            # Never replay historical XP over an already-live aggregate.
            if connection.execute(
                select(practice_progress.c.user_id).where(
                    practice_progress.c.user_id == row.user_id,
                    practice_progress.c.language_code == row.language_code.lower(),
                )
            ).first():
                continue
            connection.execute(insert(practice_progress).values(**progress_values(row)))
            counts["progress"] += 1
            for run in row.practice_sessions:
                connection.execute(insert(sessions).values(**session_values(run)))
                counts["sessions"] += 1
        for item in objects:
            saved = connection.execute(
                insert(scene_objects)
                .values(**object_values(item))
                .on_conflict_do_nothing(index_elements=[scene_objects.c.id])
                .returning(scene_objects.c.id)
            ).scalar_one_or_none()
            counts["scene_objects"] += int(saved is not None)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEMO_USERS_PATH.parent / "progress.json")
    parser.add_argument("--scene-objects", type=Path)
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
    engine = create_database_engine()
    try:
        counts = import_sessions(engine, args.path, args.scene_objects)
    except Exception:
        raise SystemExit(
            "Session import failed. Check JSON, migrations, users, language profiles, "
            "media and vocabulary references."
        ) from None
    finally:
        engine.dispose()
    print(
        f"Imported {counts}. Existing progress groups (including their sessions) "
        "and object IDs were left unchanged."
    )


if __name__ == "__main__":
    main()
