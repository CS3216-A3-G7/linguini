"""Import normalized vocabulary snapshots and optional complete encounter history."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from pydantic import TypeAdapter
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert

from app.config import DEMO_USERS_PATH
from app.database import create_database_engine
from app.repositories.implementations.postgres.vocabulary import (
    user_vocabulary_progress,
    vocabulary_encounters,
    vocabulary_items,
    vocabulary_translations,
)
from app.schemas.vocabulary import DailyVocabularyItem, VocabularyEncounter


def import_vocabulary(
    engine: Engine, path: Path, encounters_path: Path | None = None
) -> dict[str, int]:
    rows = TypeAdapter(list[DailyVocabularyItem]).validate_json(path.read_text(encoding="utf-8"))
    encounters = (
        TypeAdapter(list[VocabularyEncounter]).validate_json(
            encounters_path.read_text(encoding="utf-8")
        )
        if encounters_path
        else []
    )
    tables = [
        vocabulary_items,
        vocabulary_translations,
        user_vocabulary_progress,
        vocabulary_encounters,
    ]
    records = {table.name: {} for table in tables}

    def add(table, values):
        previous = records[table.name].get(values["id"])
        if previous is not None and previous != values:
            raise ValueError(f"Conflicting duplicate ID in {table.name}.")
        records[table.name][values["id"]] = values

    for row in rows:
        if row.progress is None or row.progress.vocabulary_item_id != row.vocabulary.id:
            raise ValueError("Missing or mismatched vocabulary progress.")
        add(vocabulary_items, row.vocabulary.model_dump(by_alias=False))
        if row.translation:
            if row.translation.vocabulary_item_id != row.vocabulary.id:
                raise ValueError("Mismatched translation reference.")
            add(vocabulary_translations, row.translation.model_dump(by_alias=False))
        add(
            user_vocabulary_progress,
            row.progress.model_dump(by_alias=False)
            | {"scene_id": row.scene_id, "topic": row.topic},
        )
    for event in encounters:
        add(vocabulary_encounters, event.model_dump(by_alias=False))
    for row in rows:
        for event_id in row.encounter_ids:
            event = records[vocabulary_encounters.name].get(event_id)
            if (
                event is None
                or event["user_id"] != row.progress.user_id
                or event["vocabulary_item_id"] != row.vocabulary.id
            ):
                raise ValueError("Encounter IDs require matching full records in --encounters.")
    counts = {table.name: 0 for table in tables}
    with engine.begin() as connection:
        for table in tables:
            for values in records[table.name].values():
                if (
                    connection.execute(
                        insert(table)
                        .values(**values)
                        .on_conflict_do_nothing(index_elements=["id"])
                        .returning(table.c.id)
                    ).scalar_one_or_none()
                    is not None
                ):
                    counts[table.name] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEMO_USERS_PATH.parent / "vocabulary.json")
    parser.add_argument("--encounters", type=Path)
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
    engine = create_database_engine()
    try:
        counts = import_vocabulary(engine, args.path, args.encounters)
    except Exception:
        raise SystemExit(
            "Vocabulary import failed. Check source data, migrations, users and media references; "
            "no partial import was committed."
        ) from None
    finally:
        engine.dispose()
    for name, count in counts.items():
        print(f"Imported {count} {name}. Existing IDs were left unchanged.")


if __name__ == "__main__":
    main()
