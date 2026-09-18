"""Explicit, transactional JSON import; repeated runs never overwrite existing users."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from pydantic import TypeAdapter
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert

from app.config import DEMO_USERS_PATH
from app.database import create_database_engine
from app.repositories.implementations.postgres.users import users
from app.schemas.users import User


def import_users(engine: Engine, path: Path) -> int:
    records = TypeAdapter(list[User]).validate_json(path.read_text(encoding="utf-8"))
    if len({user.id for user in records}) != len(records):
        raise ValueError("Duplicate user IDs in import.")
    if len({user.auth_provider_id for user in records}) != len(records):
        raise ValueError("Duplicate auth provider IDs in import.")
    imported = 0
    with engine.begin() as connection:
        for user in records:
            statement = (
                insert(users)
                .values(**user.model_dump(by_alias=False))
                .on_conflict_do_nothing(index_elements=[users.c.id])
                .returning(users.c.id)
            )
            if connection.execute(statement).scalar_one_or_none() is not None:
                imported += 1
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEMO_USERS_PATH)
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
    engine = create_database_engine()
    try:
        count = import_users(engine, args.path)
    except Exception as exc:
        # Driver exceptions can include row values; do not print credentials or personal data.
        raise SystemExit(
            "User import failed; check the JSON, database connection and migrations: "
            f"{exc}"
        ) from None
    finally:
        engine.dispose()
    print(f"Imported {count} users. Existing user IDs were left unchanged.")


if __name__ == "__main__":
    main()
