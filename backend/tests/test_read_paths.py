"""Read-path latency guarantees: no user write lock and bounded query counts."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import UUID, uuid4

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


def test_journal_detail_reads_one_entry_at_constant_cost(database):
    from datetime import date

    from app.repositories.postgres.journals import PostgresJournalRepository

    engine, owner, profile, client = database
    repository = PostgresJournalRepository(engine, owner.id)
    days = [date.today() - timedelta(days=offset) for offset in range(3)]
    ids = []
    for offset, day in enumerate(days):
        saved = client.put(
            f"/api/v1/journal/{day.isoformat()}",
            json={
                "languageProfileId": str(profile.id),
                "content": f"hola mundo numero {offset}",
                "title": f"Day {offset}",
            },
        )
        assert saved.status_code == 200, saved.text
        ids.append(UUID(saved.json()["id"]))
    expected = {row.journal.id: row for row in repository.read()}

    loaded, statements = count_statements(
        engine, lambda: repository.read_one(journal_id=ids[0])
    )
    assert loaded == expected[ids[0]]
    baseline = len(statements)
    assert baseline <= 6, baseline
    assert repository.read_one(local_date=days[1]) == expected[ids[1]]
    assert repository.read_one(journal_id=UUID(int=1)) is None

    for offset, day in enumerate(
        [date.today() - timedelta(days=days_shift) for days_shift in (10, 11)]
    ):
        assert (
            client.put(
                f"/api/v1/journal/{day.isoformat()}",
                json={
                    "languageProfileId": str(profile.id),
                    "content": "another entry",
                    "title": f"Extra {offset}",
                },
            ).status_code
            == 200
        )
    loaded_again, statements = count_statements(
        engine, lambda: repository.read_one(journal_id=ids[0])
    )
    assert loaded_again == loaded
    assert len(statements) == baseline


def test_journal_list_returns_summaries(database):
    from datetime import date

    from sqlalchemy import insert

    from app.repositories.postgres.media_assets import media_assets
    from app.schemas.media import MediaAsset

    engine, owner, profile, client = database
    asset = MediaAsset(
        owner_user_id=owner.id,
        media_type="image",
        source="userUpload",
        storage_key=f"test/{uuid4()}",
        mime_type="image/jpeg",
    )
    with engine.begin() as connection:
        connection.execute(insert(media_assets).values(**asset.model_dump(by_alias=False)))
    days = [date.today() - timedelta(days=offset) for offset in range(2)]
    saved = []
    for offset, day in enumerate(days):
        response = client.put(
            f"/api/v1/journal/{day.isoformat()}",
            json={
                "languageProfileId": str(profile.id),
                "content": "uno dos tres" if offset == 0 else "solo",
                "title": f"Day {offset}",
            },
        )
        assert response.status_code == 200, response.text
        saved.append(response.json())
    attach = client.post(
        f"/api/v1/journals/{saved[0]['id']}/media",
        json={"mediaAssetId": str(asset.id), "displayOrder": 0},
    )
    assert attach.status_code == 201, attach.text

    try:
        rows = client.get("/api/v1/journals").json()
        assert [row["id"] for row in rows] == [saved[0]["id"], saved[1]["id"]]
        first = rows[0]
        assert first["languageProfileId"] == str(profile.id)
        assert first["localDate"] == days[0].isoformat()
        assert first["title"] == "Day 0"
        assert first["wordCount"] == 3
        assert first["coverMediaAssetId"] == str(asset.id)
        assert "imageUrl" in first
        assert rows[1]["wordCount"] == 1
        assert rows[1]["coverMediaAssetId"] is None
        assert all("revisions" not in row and "journal" not in row for row in rows)
    finally:
        from sqlalchemy import delete

        from app.repositories.postgres.journals import journals

        with engine.begin() as connection:
            connection.execute(delete(journals).where(journals.c.user_id == owner.id))
