from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.schemas.media import MediaAsset
from app.schemas.sessions import CreateSessionRequest, DemoPracticeEventRequest
from app.schemas.users import LanguageProfile
from app.services.practice import PracticeConflictError, PracticeNotFoundError, PracticeService


@pytest.fixture
def context():
    profile = LanguageProfile(
        user_id=uuid4(),
        source_language_code="en",
        target_language_code="es",
        proficiency_level="A1",
    )
    profiles = MagicMock()
    profiles.list_profiles.return_value = [profile]
    rows = []
    repository = MagicMock()
    repository.read.side_effect = lambda: rows
    repository.change.side_effect = lambda fn: fn(rows)
    asset = MediaAsset(
        owner_user_id=profile.user_id,
        source="userUpload",
        media_type="image",
        storage_key="users/test/images/test.jpg",
        mime_type="image/jpeg",
    )
    media = MagicMock()
    media.get_by_ids.return_value = {asset.id: asset}
    catalog = MagicMock()
    catalog.list_scenes.return_value = []
    objects = MagicMock()
    saved = []
    objects.list_for_session.side_effect = lambda *_: list(saved)

    def save(_session, _user, results):
        saved.extend(results)
        return list(saved)

    objects.save_analysis.side_effect = save
    service = PracticeService(repository, MagicMock(), profiles, catalog, objects, None, media)
    return service, profile, asset, catalog, objects, saved


def test_uploaded_session_analysis_and_retry(context):
    service, profile, asset, catalog, objects, saved = context
    request = CreateSessionRequest(
        language_profile_id=profile.id, media_asset_id=asset.id, idempotency_key="upload-test-key"
    )
    first = service.create(request)
    assert service.create(request).session.id == first.session.id
    assert first.scene_objects == []
    assert first.analysis_mode == "placeholder"
    catalog.list_scenes.assert_not_called()
    analyzed = service.analyze(first.session.id)
    assert [obj.detected_label for obj in analyzed.scene_objects] == ["chair", "table", "plant"]
    assert all(
        obj.media_asset_id == asset.id and obj.session_id == first.session.id for obj in saved
    )
    saved[0].selection_status = "rejected"
    again = service.analyze(first.session.id)
    assert again.scene_objects[0].selection_status == "rejected"
    objects.save_analysis.assert_called_once()
    service.abandon(first.session.id)
    with pytest.raises(PracticeConflictError):
        service.analyze(first.session.id)


def test_foreign_upload_cannot_create_session(context):
    service, profile, asset, *_ = context
    asset.owner_user_id = uuid4()
    with pytest.raises(PracticeNotFoundError):
        service.create(
            CreateSessionRequest(language_profile_id=profile.id, media_asset_id=asset.id)
        )


def test_wrong_profile_and_unknown_session(context):
    service, profile, asset, *_ = context
    with pytest.raises(PracticeConflictError):
        service.create(CreateSessionRequest(language_profile_id=uuid4(), media_asset_id=asset.id))
    with pytest.raises(PracticeNotFoundError):
        service.analyze(uuid4())


@pytest.mark.parametrize("uploaded", [True, False])
def test_analysis_events_cannot_award_xp(context, uploaded):
    service, profile, asset, catalog, *_ = context
    if not uploaded:
        asset = asset.model_copy(update={"source": "preloaded", "owner_user_id": None})
        service.media.get_by_ids.return_value = {asset.id: asset}
        scene = MagicMock()
        scene.media_asset.id = asset.id
        scene.scene_id = "test-preloaded-scene"
        catalog.list_scenes.return_value = [scene]
    session = service.create(
        CreateSessionRequest(language_profile_id=profile.id, media_asset_id=asset.id)
    )
    event = DemoPracticeEventRequest(kind="analysis")
    for _ in range(3):
        assert service.record(session.session.id, event).demo_state.session_xp == 0
    assert service.repository.read()[0].xp == 0
