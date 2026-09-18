"""Import media metadata from scene fixtures or a flat asset array; no file uploads."""

import argparse
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import Engine
from sqlalchemy.dialects.postgresql import insert

from app.config import DEMO_USERS_PATH
from app.database import create_database_engine
from app.repositories.implementations.json.media_assets import read_media_assets
from app.repositories.implementations.postgres.media_assets import media_assets


def import_media_assets(engine: Engine, path: Path, *, from_scenes: bool = True) -> int:
    records = read_media_assets(path, from_scenes=from_scenes)
    imported = 0
    with engine.begin() as connection:
        for asset in records:
            statement = (
                insert(media_assets)
                .values(**asset.model_dump(by_alias=False))
                .on_conflict_do_nothing(index_elements=[media_assets.c.id])
                .returning(media_assets.c.id)
            )
            if connection.execute(statement).scalar_one_or_none() is not None:
                imported += 1
    return imported


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEMO_USERS_PATH.parent / "scenes.json")
    parser.add_argument("--format", choices=["scenes", "assets"], default="scenes")
    args = parser.parse_args()
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
    engine = create_database_engine()
    try:
        count = import_media_assets(engine, args.path, from_scenes=args.format == "scenes")
    except Exception:
        raise SystemExit(
            "Media import failed. Check JSON, migrations, owner users and duplicate storage keys."
        ) from None
    finally:
        engine.dispose()
    print(f"Imported {count} media assets. Existing IDs were left unchanged.")


if __name__ == "__main__":
    main()
