"""Read-path latency guarantees: no user write lock and bounded query counts."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID

from sqlalchemy import event, select
from test_postgres_sessions import age_session, analyze, create_run
from test_postgres_sessions import database as database

from app.repositories.postgres.users import users
from app.repositories.postgres.workflow import PostgresWorkflowRepository
from app.schemas.base import utc_now


def test_active_read_does_not_wait_on_user_write_lock(database):
    engine, owner, profile, client = database
    sid = create_run(client, profile)["session"]["id"]
    repository = PostgresWorkflowRepository(engine, owner.id)
    lock = engine.connect()
    lock.begin()
    lock.execute(select(users.c.id).where(users.c.id == owner.id).with_for_update())
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(repository.active, profile.id).result(timeout=10)
        assert result is not None and result.session.id == UUID(sid)
    finally:
        lock.rollback()
        lock.close()


def test_active_read_reaps_stale_but_not_fresh_analysis(database):
    engine, _, profile, client = database
    sid = create_run(client, profile)["session"]["id"]
    age_session(engine, UUID(sid), "analyzingScene", utc_now() - timedelta(minutes=30))
    assert client.get("/api/v1/sessions/active").json() is None
    second = create_run(client, profile, "fresh-session-key")["session"]["id"]
    age_session(engine, UUID(second), "analyzingScene", utc_now())
    active = client.get("/api/v1/sessions/active").json()
    assert active["session"]["id"] == second


def count_statements(engine, fn):
    statements = []

    def listener(_conn, _cursor, statement, _params, _context, _executemany):
        if not statement.startswith(("SET", "BEGIN", "COMMIT", "ROLLBACK", "SELECT 1")):
            statements.append(statement)

    event.listen(engine, "before_cursor_execute", listener)
    try:
        return fn(), statements
    finally:
        event.remove(engine, "before_cursor_execute", listener)


def test_session_detail_query_count(database):
    engine, _, profile, client = database
    sid = create_run(client, profile)["session"]["id"]
    detail = analyze(client, sid)
    repository = PostgresWorkflowRepository(engine, profile.user_id)

    loaded, statements = count_statements(engine, lambda: repository.get(UUID(sid), profile.id))
    assert loaded.session.id == UUID(sid)
    assert len(loaded.tasks) == len(detail["tasks"])
    assert {v.id for v in loaded.vocabulary} == {
        o.vocabulary_item_id for o in loaded.scene_objects if o.vocabulary_item_id
    }
    assert loaded.translations
    assert len(statements) <= 6, len(statements)

    for task in detail["tasks"]:
        assert client.post(f"/api/v1/tasks/{task['id']}/skip", json={}).status_code == 200
    assert client.post(f"/api/v1/sessions/{sid}/complete").status_code == 200
    draft_sid = create_run(client, profile, "draft-session-key")["session"]["id"]
    assert draft_sid != sid
    assert client.post(f"/api/v1/sessions/{draft_sid}/analyze").status_code == 200
    loaded, statements = count_statements(
        engine, lambda: repository.get(UUID(draft_sid), profile.id)
    )
    assert loaded.session.status in {"analyzingScene", "awaitingObjectReview"}
    assert loaded.scene_objects and loaded.scene_object_relations
    assert len(statements) <= 5, len(statements)


def test_progress_batches_task_counts_and_keeps_latest_scene(database):
    from sqlalchemy import update

    from app.repositories.postgres.practice import SessionBackedLearningRepository, sessions
    from app.repositories.postgres.tasks import session_tasks
    from app.repositories.postgres.vocabulary import PostgresVocabularyRepository

    engine, owner, profile, client = database
    latest = None
    for index in range(3):
        latest = UUID(create_run(client, profile, f"progress-{index}")["session"]["id"])
        detail = analyze(client, str(latest))
        task_ids = [UUID(task["id"]) for task in detail["tasks"]]
        with engine.begin() as connection:
            connection.execute(
                update(session_tasks)
                .where(session_tasks.c.session_id == latest)
                .values(status="skipped", skipped_at=utc_now())
            )
            if index:
                connection.execute(
                    update(session_tasks)
                    .where(session_tasks.c.id.in_(task_ids[:index]))
                    .values(status="completed", completed_at=utc_now(), skipped_at=None)
                )
            connection.execute(
                update(sessions).where(sessions.c.id == latest).values(
                    status="completed", started_at=utc_now(), completed_at=utc_now()
                )
            )

    repository = SessionBackedLearningRepository(
        engine, owner.id, PostgresVocabularyRepository(engine)
    )
    progress, statements = count_statements(
        engine, lambda: repository.get_progress(owner.id, "es")
    )
    assert len(statements) == 2
    assert len(progress.scenarios) == 1
    scene = progress.scenarios[0]
    assert scene.session_id == latest
    assert scene.completed_task_count == 2
    assert scene.total_task_count == len(task_ids)
    assert scene.status == "completed"
    assert repository.get_progress(owner.id, "fr").scenarios == []
