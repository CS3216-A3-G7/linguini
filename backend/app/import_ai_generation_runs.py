"""Import an array of historical AiGenerationRun records without overwriting live runs."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from pydantic import TypeAdapter
from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert

from app.database import create_database_engine
from app.repositories.implementations.postgres.ai import ai_generation_runs, same_identity
from app.schemas.ai import AiGenerationRun


def import_ai_generation_runs(engine: Engine, path: Path) -> int:
    records = TypeAdapter(list[AiGenerationRun]).validate_json(path.read_text(encoding="utf-8"))
    if len({run.id for run in records}) != len(records):
        raise ValueError("Duplicate AI run IDs in import.")
    imported = 0
    with engine.begin() as connection:
        for run in records:
            saved = connection.execute(
                insert(ai_generation_runs)
                .values(**run.model_dump(by_alias=False))
                .on_conflict_do_nothing(index_elements=[ai_generation_runs.c.id])
                .returning(ai_generation_runs.c.id)
            ).scalar_one_or_none()
            if saved is not None:
                imported += 1
            else:
                row = (
                    connection.execute(
                        select(ai_generation_runs)
                        .where(ai_generation_runs.c.id == run.id)
                        .with_for_update()
                    )
                    .mappings()
                    .one()
                )
                if not same_identity(AiGenerationRun.model_validate(dict(row)), run):
                    raise ValueError("Existing AI run ID has a different identity.")
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
    engine = create_database_engine()
    try:
        count = import_ai_generation_runs(engine, args.path)
    except Exception:
        raise SystemExit(
            "AI run import failed. Check records, migrations, users and session/journal ownership."
        ) from None
    finally:
        engine.dispose()
    print(f"Imported {count} AI runs. Existing IDs were left unchanged.")


if __name__ == "__main__":
    main()
