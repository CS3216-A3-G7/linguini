from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.repositories.postgres.workflow import PostgresWorkflowRepository
from app.repositories.practice import PracticeConflictError
from app.schemas.sessions import ReviewPracticeRequest


def test_review_requires_unique_nonempty_selection_and_in_bounds_positions():
    object_id = uuid4()
    for body in [
        {"acceptedObjectIds": []},
        {"acceptedObjectIds": [str(object_id), str(object_id)]},
        {
            "acceptedObjectIds": [],
            "addedObjects": [{"id": str(object_id), "label": "window", "x": 1, "y": 0.2}],
        },
    ]:
        with pytest.raises(ValidationError):
            ReviewPracticeRequest.model_validate(body)
    review = ReviewPracticeRequest.model_validate(
        {
            "acceptedObjectIds": [],
            "addedObjects": [
                {
                    "id": str(object_id),
                    "label": " window ",
                    "x": 0.99,
                    "y": 0,
                }
            ],
        }
    )
    assert review.added_objects[0].label == "window"


@pytest.mark.parametrize("status", ["completed", "abandoned", "failed"])
def test_review_cannot_change_terminal_sessions(status):
    repo = PostgresWorkflowRepository(None, uuid4())
    connection = MagicMock()

    @contextmanager
    def transaction():
        yield connection

    repo.transaction = transaction
    repo._session = lambda *args: SimpleNamespace(status=status, plan_version="v1")
    with pytest.raises(PracticeConflictError):
        repo.review(uuid4(), uuid4(), ReviewPracticeRequest(accepted_object_ids=[uuid4()]))
    connection.execute.assert_not_called()


@pytest.mark.parametrize("status", ["inProgress", "completed", "skipped"])
def test_review_cannot_replace_started_tasks(status):
    repo = PostgresWorkflowRepository(None, uuid4())
    connection = MagicMock()

    @contextmanager
    def transaction():
        yield connection

    repo.transaction = transaction
    repo._session = lambda *args: SimpleNamespace(status="inProgress", plan_version="v1")
    repo._tasks = lambda *args: [SimpleNamespace(status=status)]
    with pytest.raises(PracticeConflictError):
        repo.review(uuid4(), uuid4(), ReviewPracticeRequest(accepted_object_ids=[uuid4()]))
    connection.execute.assert_not_called()


def test_review_rebuilds_tasks_only_for_selected_objects():
    from uuid import uuid5

    from app.schemas.media import SceneObject
    from app.schemas.vocabulary import VocabularyItem, VocabularyTranslation

    session_id, profile_id, asset_id = uuid4(), uuid4(), uuid4()
    words = [
        VocabularyItem(language_code="es", lemma=text, display_text=text, part_of_speech="noun")
        for text in ["silla", "mesa"]
    ]
    objects = [
        SceneObject(
            session_id=session_id,
            media_asset_id=asset_id,
            detected_label=label,
            vocabulary_item_id=word.id,
            selection_status="accepted",
            bounding_box={"x": 0.2, "y": 0.3, "width": 0.01, "height": 0.01},
        )
        for word, label in zip(words, ["chair", "table"], strict=True)
    ]
    translations = [
        VocabularyTranslation(
            vocabulary_item_id=word.id, source_language_code="en", translated_text=label
        )
        for word, label in zip(words, ["chair", "table"], strict=True)
    ]
    detail = SimpleNamespace(scene_objects=objects, vocabulary=words, translations=translations)
    repo = PostgresWorkflowRepository(None, uuid4())
    connection = MagicMock()
    connection.execute.return_value.first.return_value = None
    connection.execute.return_value.mappings.return_value.one.return_value = {
        "source_language_code": "en",
        "target_language_code": "es",
    }

    @contextmanager
    def transaction():
        yield connection

    repo.transaction = transaction
    repo._session = lambda *args: SimpleNamespace(
        id=session_id, status="inProgress", plan_version="v1", started_at=None
    )
    repo._tasks = lambda *args: []
    repo._detail = lambda *args: detail
    repo.review(session_id, profile_id, ReviewPracticeRequest(accepted_object_ids=[objects[1].id]))
    inserted = [
        call.args[0].compile().params
        for call in connection.execute.call_args_list
        if getattr(call.args[0], "is_insert", False) and call.args[0].table.name == "session_tasks"
    ]
    assert len(inserted) == 8
    assert all(task["scene_object_id"] == objects[1].id for task in inserted)
    introduction = next(task for task in inserted if task["kind"] == "vocabularyIntroduction")
    assert introduction["public_content"]["targetText"] == "mesa"
    assert introduction["public_content"]["translation"] == "table"
    # Same pending session can be reviewed again without changing generated task identity.
    assert introduction["id"] == uuid5(session_id, "placeholder-v1:vocabularyIntroduction")


def test_unknown_word_cannot_create_catalog_entries():
    repo = PostgresWorkflowRepository(None, uuid4())
    connection = MagicMock()
    connection.execute.return_value.mappings.return_value.first.return_value = None
    with pytest.raises(PracticeConflictError, match="not in the vocabulary"):
        repo._catalog_word(
            connection, {"target_language_code": "es", "source_language_code": "en"}, "unknown"
        )
    assert all(call.args[0].is_select for call in connection.execute.call_args_list)


def test_analysis_saves_draft_without_scene_objects_or_tasks(monkeypatch):
    from app.schemas.media import MediaAsset, SceneObject
    from app.schemas.sessions import Session

    owner, profile = uuid4(), uuid4()
    asset = MediaAsset(
        owner_user_id=owner,
        source="userUpload",
        media_type="image",
        storage_key="test/photo.jpg",
        mime_type="image/jpeg",
    )
    session = Session(user_id=owner, language_profile_id=profile, scene_media_asset_id=asset.id)
    obj = SceneObject(
        session_id=session.id,
        media_asset_id=asset.id,
        detected_label="chair",
        bounding_box={"x": 0.1, "y": 0.1, "width": 0.1, "height": 0.1},
    )
    repo = PostgresWorkflowRepository(None, owner)
    connection = MagicMock()
    connection.execute.return_value.scalar_one_or_none.return_value = None
    connection.execute.return_value.mappings.return_value.one.side_effect = [asset.model_dump(), {}]

    @contextmanager
    def transaction():
        yield connection

    repo.transaction = transaction
    repo._session = lambda *args: session
    repo._detail = lambda *args: "draft detail"
    monkeypatch.setattr(
        "app.repositories.postgres.workflow.build_objects", lambda *args: ([obj], [], [])
    )
    assert repo.analyze(session.id, profile) == "draft detail"
    writes = [
        call.args[0] for call in connection.execute.call_args_list if not call.args[0].is_select
    ]
    assert len(writes) == 2
    assert all(write.table.name == "sessions" for write in writes)
    draft = writes[1].compile().params["analysis_draft"]
    assert draft[0]["id"] == str(obj.id)
    assert draft[0]["selection_status"] == "suggested"
