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
from sqlalchemy.dialects.postgresql import ENUM, JSONB

from app.schemas.enums import SessionFailureCode, SessionStatus
from app.schemas.progress import StoredProgress

sessions = Table(
    "sessions",
    MetaData(),
    Column("id", Uuid, primary_key=True),
    Column("user_id", Uuid, nullable=False),
    Column("language_profile_id", Uuid, nullable=False),
    Column("scene_media_asset_id", Uuid, nullable=False),
    Column(
        "session_status",
        ENUM(
            SessionStatus,
            name="session_status",
            schema="public",
            values_callable=lambda statuses: [status.value for status in statuses],
            create_type=False,
        ),
        key="status",
        nullable=False,
    ),
    Column("started_at", DateTime(timezone=True)),
    Column("completed_at", DateTime(timezone=True)),
    Column("abandoned_at", DateTime(timezone=True)),
    Column("analysis_draft", JSONB(none_as_null=True)),
    Column("session_title", String),
    Column("session_summary", String),
    Column(
        "failure_code",
        ENUM(
            SessionFailureCode,
            name="session_failure_code",
            schema="public",
            values_callable=lambda codes: [code.value for code in codes],
            create_type=False,
        ),
    ),
    Column("idempotency_key", String(200)),
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
            task_counts = (
                select(
                    session_tasks.c.session_id,
                    func.count().label("total_task_count"),
                    func.count().filter(session_tasks.c.status == "completed").label(
                        "completed_task_count"
                    ),
                )
                .join(sessions, sessions.c.id == session_tasks.c.session_id)
                .where(sessions.c.user_id == user_id)
                .group_by(session_tasks.c.session_id)
                .subquery()
            )
            query = (
                select(
                    sessions, preloaded_scenes.c.slug, preloaded_scenes.c.title,
                    task_counts.c.total_task_count, task_counts.c.completed_task_count,
                )
                .join(task_counts, task_counts.c.session_id == sessions.c.id)
                .join(language_profiles, language_profiles.c.id == sessions.c.language_profile_id)
                .outerjoin(
                    preloaded_scenes,
                    preloaded_scenes.c.media_asset_id == sessions.c.scene_media_asset_id,
                )
                .where(
                    sessions.c.user_id == user_id,
                    sessions.c.status.in_(["inProgress", "completed"]),
                )
                .order_by(sessions.c.started_at)
            )
            if language_code:
                query = query.where(
                    func.lower(language_profiles.c.target_language_code) == language_code.lower()
                )
            scenarios = {}
            for row in connection.execute(query).mappings():
                scene_id = row["slug"] or str(row["id"])
                scenarios[scene_id] = ScenarioProgress(
                    scene_id=scene_id,
                    session_id=row["id"],
                    media_asset_id=row["scene_media_asset_id"],
                    title=row["title"] or "Your uploaded photo",
                    status="completed" if row["status"] == "completed" else "in-progress",
                    completed_task_count=row["completed_task_count"],
                    total_task_count=row["total_task_count"],
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
