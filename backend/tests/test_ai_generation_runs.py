import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import delete, insert, text, update
from sqlalchemy.exc import IntegrityError, OperationalError
from test_postgres_sessions import create_run
from test_postgres_sessions import database as database

from app.import_ai_generation_runs import import_ai_generation_runs
from app.repositories.ai import AiRunConflictError, AiRunNotFoundError, AiRunStorageError
from app.repositories.implementations.postgres.ai import (
    PostgresAiGenerationRunRepository,
    ai_generation_runs,
)
from app.repositories.implementations.postgres.journals import PostgresJournalRepository, journals
from app.repositories.implementations.postgres.users import users
from app.schemas.ai import AiGenerationRun, AiGenerationRunCompletion
from app.schemas.base import utc_now
from app.schemas.journals import Journal, JournalDetailResponse
from app.schemas.users import User


def run_record(**changes):
    return AiGenerationRun.model_validate(
        {
            "feature": "sceneAnalysis",
            "model_name": "test-model",
            "prompt_version": "v1",
            "schema_version": "v1",
            **changes,
        }
    )


@pytest.fixture
def context(database):
    engine, owner, profile, client = database
    session = create_run(client, profile)["session"]
    journal = Journal(
        user_id=owner.id, language_profile_id=profile.id, local_date=date.today(), timezone="UTC"
    )
    PostgresJournalRepository(engine, owner.id).change(
        lambda rows: rows.append(JournalDetailResponse(journal=journal))
    )
    repository = PostgresAiGenerationRunRepository(engine, owner.id)
    run = run_record(user_id=owner.id, session_id=session["id"], journal_id=journal.id)
    return engine, owner, journal, repository, run


@pytest.mark.parametrize(
    "changes",
    [
        {"session_id": uuid4()},
        {"journal_id": uuid4()},
        {"status": "pending", "completed_at": utc_now()},
        {"status": "succeeded"},
        {"status": "failed", "completed_at": utc_now()},
        {"status": "failed", "completed_at": utc_now(), "error_code": " "},
        {"error_code": "bad"},
        {"input_tokens": -1},
    ],
)
def test_schema_rejects_invalid_runs(changes):
    with pytest.raises(ValidationError):
        run_record(**changes)


def test_create_finish_and_retry(context):
    _, owner, journal, repository, run = context
    assert repository.create(run).status == "pending"
    # A reconstructed job with a stable UUID must not create another run.
    retry = run_record(
        id=run.id, user_id=owner.id, session_id=run.session_id, journal_id=journal.id
    )
    assert repository.create(retry).created_at == run.created_at
    result = AiGenerationRunCompletion(
        status="succeeded",
        input_tokens=3_000_000_000,
        output_tokens=20,
        latency_ms=80,
        validation_passed=True,
        output_reference="results/run.json",
    )
    saved = repository.finish(run.id, result)
    assert saved.completed_at is not None and saved.status == "succeeded"
    assert saved.input_tokens == 3_000_000_000
    assert repository.finish(run.id, result) == saved
    assert repository.create(retry) == saved
    assert repository.get(run.id) == saved
    assert repository.list_runs(session_id=run.session_id, journal_id=journal.id) == [saved]
    with pytest.raises(AiRunConflictError):
        repository.finish(run.id, AiGenerationRunCompletion(status="failed", error_code="timeout"))
    with pytest.raises(AiRunConflictError):
        repository.create(retry.model_copy(update={"prompt_version": "v2"}))


def test_concurrent_create_and_conflicting_finish(context):
    _, _, _, repository, run = context
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(lambda _: repository.create(run), range(4)))
    assert len({record.id for record in records}) == 1

    def finish(status):
        result = AiGenerationRunCompletion(
            status=status, **({"error_code": "timeout"} if status == "failed" else {})
        )
        try:
            return repository.finish(run.id, result).status.value
        except AiRunConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(finish, ["succeeded", "failed"]))
    assert results.count("conflict") == 1
    assert repository.get(run.id).status.value in results


def test_scope_and_composite_ownership(context):
    engine, owner, journal, repository, run = context
    repository.create(run)
    other = User(display_name="Other AI owner", auth_provider_id=f"test-{uuid4()}")
    with engine.begin() as connection:
        connection.execute(insert(users).values(**other.model_dump(by_alias=False)))
    other_repository = PostgresAiGenerationRunRepository(engine, other.id)
    assert other_repository.get(run.id) is None
    assert other_repository.list_runs() == []
    with pytest.raises(AiRunNotFoundError):
        other_repository.finish(run.id, AiGenerationRunCompletion(status="succeeded"))
    for links in ({"session_id": run.session_id}, {"journal_id": journal.id}):
        with pytest.raises(AiRunConflictError):
            other_repository.create(run_record(user_id=other.id, **links))
    with pytest.raises(AiRunConflictError):
        repository.create(run_record(user_id=other.id))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        values = run.model_dump(by_alias=False) | {"id": uuid4(), "user_id": None}
        connection.execute(insert(ai_generation_runs).values(**values))
    with engine.begin() as connection:
        connection.execute(delete(users).where(users.c.id == other.id))


def test_system_runs_are_explicitly_separate(context):
    engine, _, _, repository, _ = context
    system = PostgresAiGenerationRunRepository(engine, None)
    run = system.create(run_record())
    assert system.get(run.id) == run
    assert repository.get(run.id) is None
    failed = system.finish(
        run.id,
        AiGenerationRunCompletion(
            status="failed", error_code="schema_invalid", validation_passed=False
        ),
    )
    assert failed.validation_passed is False
    assert (
        system.finish(
            run.id,
            AiGenerationRunCompletion(
                status="failed", error_code="schema_invalid", validation_passed=False
            ),
        )
        == failed
    )
    with engine.begin() as connection:
        connection.execute(delete(ai_generation_runs).where(ai_generation_runs.c.id == run.id))


@pytest.mark.parametrize(
    "values",
    [
        {"status": "succeeded"},
        {"status": "failed", "completed_at": utc_now(), "error_code": ""},
        {"latency_ms": -1},
        {"feature": "invented"},
        {"model_name": " "},
    ],
)
def test_database_constraints(context, values):
    engine, _, _, _, run = context
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            insert(ai_generation_runs).values(**(run.model_dump(by_alias=False) | values))
        )


def test_terminal_immutability_and_context_cascade(context):
    engine, owner, journal, repository, run = context
    repository.create(run)
    repository.finish(run.id, AiGenerationRunCompletion(status="succeeded"))
    for changes in (
        {"status": "pending", "completed_at": None},
        {"output_tokens": 123},
        {"prompt_version": "v2"},
    ):
        with pytest.raises(IntegrityError), engine.begin() as connection:
            connection.execute(
                update(ai_generation_runs)
                .where(ai_generation_runs.c.id == run.id)
                .values(**changes)
            )
    with engine.begin() as connection:
        assert connection.execute(
            text(
                "SELECT relrowsecurity FROM pg_class "
                "WHERE oid='public.ai_generation_runs'::regclass"
            )
        ).scalar_one()
        connection.execute(delete(journals).where(journals.c.id == journal.id))
    assert repository.get(run.id) is None


def test_import_rollback_and_preserves_live_results(context, tmp_path):
    engine, owner, _, repository, run = context
    failed = run_record(
        user_id=owner.id, status="failed", completed_at=utc_now(), error_code="timeout"
    )
    path = tmp_path / "ai_runs.json"
    bad = run_record(user_id=owner.id, session_id=uuid4())
    path.write_text(json.dumps([failed.model_dump(mode="json"), bad.model_dump(mode="json")]))
    with pytest.raises(IntegrityError):
        import_ai_generation_runs(engine, path)
    assert repository.list_runs() == []
    path.write_text(json.dumps([failed.model_dump(mode="json"), run.model_dump(mode="json")]))
    assert import_ai_generation_runs(engine, path) == 2
    repository.finish(run.id, AiGenerationRunCompletion(status="succeeded"))
    assert import_ai_generation_runs(engine, path) == 0
    assert repository.get(run.id).status == "succeeded"
    assert repository.get(failed.id).error_code == "timeout"
    conflicting = run.model_copy(update={"model_name": "different-model"})
    path.write_text(json.dumps([conflicting.model_dump(mode="json")]))
    with pytest.raises(ValueError):
        import_ai_generation_runs(engine, path)


def test_duplicate_import_and_safe_errors(tmp_path):
    engine = MagicMock()
    run = run_record()
    path = tmp_path / "ai_runs.json"
    path.write_text(json.dumps([run.model_dump(mode="json")] * 2))
    with pytest.raises(ValueError):
        import_ai_generation_runs(engine, path)
    engine.begin.assert_not_called()
    engine.connect.side_effect = OperationalError("select", {}, Exception("secret"))
    with pytest.raises(AiRunStorageError, match="Unable to load AI run"):
        PostgresAiGenerationRunRepository(engine, None).get(uuid4())
