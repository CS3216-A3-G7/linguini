"""Session table definitions and progress derived from normalized encounters."""

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    Uuid,
    func,
    select,
)

from app.schemas.progress import StoredProgress

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
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    schema="public",
)


class SessionBackedLearningRepository:
    def __init__(self, engine, user_id, vocabulary):
        self.engine = engine
        self.user_id = user_id
        self.vocabulary = vocabulary

    def get_progress(self, user_id, language_code=None):
        from app.repositories.postgres.language_profiles import language_profiles
        from app.repositories.postgres.scenes import preloaded_scenes
        from app.repositories.postgres.tasks import session_tasks
        from app.repositories.postgres.vocabulary import vocabulary_encounters, vocabulary_items
        from app.schemas.progress import ScenarioProgress

        if user_id != self.user_id:
            return None
        with self.engine.connect() as connection:
            query = (
                select(func.count())
                .select_from(vocabulary_encounters)
                .join(
                    vocabulary_items,
                    vocabulary_items.c.id == vocabulary_encounters.c.vocabulary_item_id,
                )
                .where(vocabulary_encounters.c.user_id == user_id)
            )
            if language_code:
                query = query.where(
                    func.lower(vocabulary_items.c.language_code) == language_code.lower()
                )
            xp = connection.execute(query).scalar_one() * 5
            query = (
                select(sessions, preloaded_scenes.c.slug, preloaded_scenes.c.title)
                .join(language_profiles, language_profiles.c.id == sessions.c.language_profile_id)
                .outerjoin(
                    preloaded_scenes,
                    preloaded_scenes.c.media_asset_id == sessions.c.scene_media_asset_id,
                )
                .where(
                    sessions.c.user_id == user_id,
                    sessions.c.plan_version.is_not(None),
                    sessions.c.status.in_(["inProgress", "completed"]),
                )
                .order_by(sessions.c.created_at)
            )
            if language_code:
                query = query.where(
                    func.lower(language_profiles.c.target_language_code) == language_code.lower()
                )
            scenarios = {}
            for row in connection.execute(query).mappings():
                states = (
                    connection.execute(
                        select(session_tasks.c.status).where(
                            session_tasks.c.session_id == row["id"]
                        )
                    )
                    .scalars()
                    .all()
                )
                if not states:
                    continue
                scene_id = row["slug"] or str(row["id"])
                scenarios[scene_id] = ScenarioProgress(
                    scene_id=scene_id,
                    session_id=row["id"],
                    media_asset_id=row["scene_media_asset_id"],
                    title=row["title"] or "Your uploaded photo",
                    status="completed" if row["status"] == "completed" else "in-progress",
                    completed_task_count=states.count("completed"),
                    total_task_count=len(states),
                    level="Starter",
                )
            return StoredProgress(
                user_id=user_id,
                language_code=language_code or "es",
                xp=xp,
                scenarios=list(scenarios.values()),
                leaderboard=[],
            )

    def list_vocabulary(self, user_id):
        return self.vocabulary.list_vocabulary(user_id)
