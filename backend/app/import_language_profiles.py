"""Import JSON profiles transactionally after importing their users."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from pydantic import TypeAdapter
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert

from app.config import DEMO_USERS_PATH
from app.database import create_database_engine
from app.repositories.implementations.postgres.language_profiles import language_profiles, lock_user
from app.schemas.users import LanguageProfile


def import_language_profiles(engine: Engine, path: Path) -> int:
    records = TypeAdapter(list[LanguageProfile]).validate_json(path.read_text(encoding="utf-8"))
    if len({row.id for row in records}) != len(records):
        raise ValueError("Duplicate language profile IDs in import.")
    pairs = {
        (row.user_id, row.source_language_code.lower(), row.target_language_code.lower())
        for row in records
    }
    if len(pairs) != len(records):
        raise ValueError("Duplicate language pairs in import.")
    active_users = [row.user_id for row in records if row.is_active]
    if len(set(active_users)) != len(active_users):
        raise ValueError("Multiple active language profiles for one user in import.")
    imported = 0
    with engine.begin() as connection:
        # Consistent lock ordering prevents deadlocks between overlapping imports.
        for user_id in sorted({row.user_id for row in records}):
            lock_user(connection, user_id)
        for profile in records:
            statement = (
                insert(language_profiles)
                .values(**profile.model_dump(by_alias=False))
                .on_conflict_do_nothing(index_elements=[language_profiles.c.id])
                .returning(language_profiles.c.id)
            )
            if connection.execute(statement).scalar_one_or_none() is not None:
                imported += 1
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path", type=Path, default=DEMO_USERS_PATH.parent / "language_profiles.json"
    )
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
    engine = create_database_engine()
    try:
        count = import_language_profiles(engine, args.path)
    except Exception:
        raise SystemExit(
            "Language profile import failed. Check migrations and JSON; import users first. "
            "Conflicting language pairs or active profiles must be resolved before retrying."
        ) from None
    finally:
        engine.dispose()
    print(f"Imported {count} language profiles. Existing IDs were left unchanged.")


if __name__ == "__main__":
    main()
