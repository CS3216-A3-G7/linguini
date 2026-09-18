"""Import complete JournalDetailResponse records atomically; preserve existing journals."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from pydantic import TypeAdapter
from sqlalchemy import Engine, select

from app.config import DEMO_USERS_PATH
from app.database import create_database_engine
from app.repositories.implementations.postgres.journals import insert_entries, journals
from app.repositories.implementations.postgres.users import users
from app.repositories.journals import validate_entries
from app.schemas.journals import JournalDetailResponse


def import_journals(engine: Engine, path: Path) -> dict[str, int]:
    rows = TypeAdapter(list[JournalDetailResponse]).validate_json(path.read_text(encoding="utf-8"))
    validate_entries(rows)
    counts = {"journals": 0, "media": 0, "revisions": 0, "suggestions": 0, "word_mentions": 0}
    with engine.begin() as connection:
        for owner in sorted({row.journal.user_id for row in rows}, key=str):
            if (
                connection.execute(
                    select(users.c.id).where(users.c.id == owner).with_for_update()
                ).scalar_one_or_none()
                is None
            ):
                raise ValueError("Import journal users first.")
        pending = []
        for entry in rows:
            existing = (
                connection.execute(select(journals).where(journals.c.id == entry.journal.id))
                .mappings()
                .one_or_none()
            )
            if existing is not None:
                if any(
                    existing[field] != getattr(entry.journal, field)
                    for field in ("user_id", "language_profile_id", "local_date", "timezone")
                ):
                    raise ValueError("Existing journal ID has a different identity.")
                continue
            pending.append(entry)
            counts["journals"] += 1
            for name in ("media", "revisions", "suggestions", "word_mentions"):
                counts[name] += len(getattr(entry, name))
        insert_entries(connection, pending)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEMO_USERS_PATH.parent / "journals.json")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
    engine = create_database_engine()
    try:
        counts = import_journals(engine, args.path)
    except Exception:
        raise SystemExit(
            "Journal import failed. Check records, migrations, users, profiles, "
            "media, vocabulary and encounter references."
        ) from None
    finally:
        engine.dispose()
    print(f"Imported {counts}. Existing journals and their children were left unchanged.")


if __name__ == "__main__":
    main()
