from types import SimpleNamespace
from uuid import uuid4

from app.repositories.postgres.workflow import PostgresWorkflowRepository


def test_grouped_vocabulary_introduction_uses_one_encounter_id_per_word(
    monkeypatch,
) -> None:
    captured = []
    monkeypatch.setattr(
        "app.repositories.postgres.workflow.record_vocabulary_evidence",
        lambda _connection, **kwargs: captured.append(kwargs["encounter"]),
    )
    repository = object.__new__(PostgresWorkflowRepository)
    repository.user_id = uuid4()
    task = SimpleNamespace(
        vocabulary_item_id=uuid4(), session_id=uuid4(), id=uuid4()
    )
    event_id = uuid4()
    first_word, second_word = uuid4(), uuid4()

    repository._encounter(
        object(), task, event_id, "correct", introduced=True, vocabulary_item_id=first_word
    )
    repository._encounter(
        object(), task, event_id, "correct", introduced=True, vocabulary_item_id=second_word
    )

    assert [event.vocabulary_item_id for event in captured] == [first_word, second_word]
    assert captured[0].id != captured[1].id
