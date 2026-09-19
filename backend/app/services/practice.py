from uuid import UUID

from app.repositories.media_assets import MediaAssetRepository
from app.repositories.practice import PracticeRepository
from app.repositories.scene_objects import SceneObjectRepository
from app.repositories.tasks import TaskRepository
from app.schemas.base import utc_now
from app.schemas.enums import MediaSource, MediaType, SessionStatus
from app.schemas.media import ReviewSceneObjectsRequest
from app.schemas.progress import ScenarioProgress, StoredProgress
from app.schemas.sessions import (
    CreateSessionRequest,
    DemoPracticeEventRequest,
    DemoPracticeState,
    Session,
    SessionDetailResponse,
    StoredDemoSession,
)
from app.schemas.tasks import SessionProgress, SessionTaskPublic
from app.services.image_analysis import PlaceholderImageExtractor
from app.services.language_profiles import LanguageProfileService
from app.services.scenes import SceneService
from app.services.users import UserService


class PracticeNotFoundError(Exception):
    pass


class PracticeConflictError(Exception):
    pass


class PracticeService:
    def __init__(
        self,
        repository: PracticeRepository,
        users: UserService,
        profiles: LanguageProfileService,
        scenes: SceneService,
        scene_objects: SceneObjectRepository | None = None,
        tasks: TaskRepository | None = None,
        media: MediaAssetRepository | None = None,
        extractor: PlaceholderImageExtractor | None = None,
    ) -> None:
        self.repository = repository
        self.users = users
        self.profiles = profiles
        self.scenes = scenes
        self.scene_objects = scene_objects
        self.tasks = tasks
        self.media = media
        self.extractor = extractor or PlaceholderImageExtractor()

    def _profile(self):
        self.profiles.active_language()
        return next(row for row in self.profiles.list_profiles() if row.is_active)

    @staticmethod
    def _detail(run: StoredDemoSession) -> SessionDetailResponse:
        return SessionDetailResponse(
            session=run.session,
            demo_state=run.state,
            analysis_mode="placeholder" if run.state.scene_id.startswith("upload:") else None,
        )

    def _attach_objects(self, detail: SessionDetailResponse) -> SessionDetailResponse:
        if self.scene_objects is not None:
            detail.scene_objects = self.scene_objects.list_for_session(
                detail.session.id, detail.session.user_id
            )
        if self.tasks is not None:
            records = self.tasks.list_for_session(detail.session.id, detail.session.user_id)
            detail.tasks = [SessionTaskPublic.from_internal(task) for task in records]
            if records:
                completed = sum(task.status == "completed" for task in records)
                skipped = sum(task.status == "skipped" for task in records)
                detail.progress = SessionProgress(
                    terminal_task_count=completed + skipped,
                    completed_task_count=completed,
                    skipped_task_count=skipped,
                    total_task_count=len(records),
                )
                detail.next_task_id = next(
                    (task.id for task in records if task.status not in {"completed", "skipped"}),
                    None,
                )
        return detail

    def _find(self, rows: list[StoredProgress], session_id: UUID, profile=None):
        profile = profile or self._profile()
        for progress in rows:
            if progress.user_id != profile.user_id:
                continue
            for run in progress.practice_sessions:
                if run.session.id == session_id and run.session.language_profile_id == profile.id:
                    return progress, run
        raise PracticeNotFoundError("Session not found for the active language.")

    def get(self, session_id: UUID) -> SessionDetailResponse:
        _, run = self._find(self.repository.read(), session_id)
        return self._attach_objects(self._detail(run))

    def active(self) -> SessionDetailResponse | None:
        profile = self._profile()
        runs = [
            run
            for row in self.repository.read()
            if row.user_id == profile.user_id
            for run in row.practice_sessions
            if run.session.language_profile_id == profile.id
            and run.session.status == SessionStatus.IN_PROGRESS
        ]
        return self._attach_objects(self._detail(runs[-1])) if runs else None

    def create(self, request: CreateSessionRequest) -> SessionDetailResponse:
        profile = self._profile()
        if request.language_profile_id != profile.id:
            raise PracticeConflictError("Select the active language profile.")
        asset = (
            self.media.get_by_ids([request.media_asset_id]).get(request.media_asset_id)
            if self.media
            else None
        )
        uploaded = (
            asset is not None
            and asset.owner_user_id == profile.user_id
            and asset.media_type == MediaType.IMAGE
            and asset.source in (MediaSource.CAMERA, MediaSource.USER_UPLOAD)
        )
        scene = (
            None
            if uploaded
            else next(
                (
                    row
                    for row in self.scenes.list_scenes(profile.target_language_code)
                    if row.media_asset.id == request.media_asset_id
                ),
                None,
            )
        )
        if scene is None and not uploaded:
            raise PracticeNotFoundError("Scene not found for the active language.")

        def change(rows: list[StoredProgress]) -> SessionDetailResponse:
            progress = next(
                (
                    row
                    for row in rows
                    if row.user_id == profile.user_id
                    and row.language_code == profile.target_language_code
                ),
                None,
            )
            if progress is None:
                progress = StoredProgress(
                    user_id=profile.user_id,
                    language_code=profile.target_language_code,
                    xp=0,
                    scenarios=[],
                    leaderboard=[],
                )
                rows.append(progress)
            for run in progress.practice_sessions:
                if (
                    request.idempotency_key
                    and run.idempotency_key == request.idempotency_key
                    and run.session.language_profile_id == profile.id
                ):
                    if run.session.scene_media_asset_id != request.media_asset_id:
                        raise PracticeConflictError(
                            "Idempotency key already used for another scene."
                        )
                    return self._detail(run)
            for previous in progress.practice_sessions:
                if (
                    previous.session.status == SessionStatus.IN_PROGRESS
                    and previous.session.language_profile_id == profile.id
                ):
                    previous.session.abandoned_at = utc_now()
                    previous.session.status = SessionStatus.ABANDONED
            run = StoredDemoSession(
                session=Session(
                    user_id=profile.user_id,
                    language_profile_id=profile.id,
                    scene_media_asset_id=request.media_asset_id,
                    status=SessionStatus.IN_PROGRESS,
                    started_at=utc_now(),
                ),
                state=DemoPracticeState(
                    scene_id=f"upload:{asset.id}" if uploaded else scene.scene_id
                ),
                idempotency_key=request.idempotency_key,
            )
            progress.practice_sessions.append(run)
            return self._detail(run)

        return self._attach_objects(self.repository.change(change))

    def analyze(self, session_id: UUID) -> SessionDetailResponse:
        detail = self.get(session_id)
        if detail.session.status != SessionStatus.IN_PROGRESS:
            raise PracticeConflictError("Session is no longer active.")
        if (
            detail.analysis_mode != "placeholder"
            or self.media is None
            or self.scene_objects is None
        ):
            raise PracticeConflictError("Analysis requires an uploaded image session.")
        asset = self.media.get_by_ids([detail.session.scene_media_asset_id]).get(
            detail.session.scene_media_asset_id
        )
        if (
            asset is None
            or asset.owner_user_id != detail.session.user_id
            or asset.media_type != MediaType.IMAGE
        ):
            raise PracticeNotFoundError("Image not found.")
        if not detail.scene_objects:
            objects = self.extractor.extract(asset, session_id)
            detail.scene_objects = self.scene_objects.save_analysis(
                session_id, detail.session.user_id, objects
            )
        return detail

    def record(self, session_id: UUID, event: DemoPracticeEventRequest) -> SessionDetailResponse:
        profile = self._profile()
        progress, initial = self._find(self.repository.read(), session_id, profile)
        scene = (
            None
            if event.kind == "analysis"
            else self.scenes.get_scene(initial.state.scene_id, progress.language_code)
        )

        def change(rows: list[StoredProgress]) -> SessionDetailResponse:
            progress, run = self._find(rows, session_id, profile)
            state = run.state
            key = f"{event.kind}:{event.item_id}"
            duplicate = (
                event.kind == "analysis"
                and state.analysis_scored
                or event.kind == "task"
                and event.item_id in state.completed_task_ids
                or key in state.scored_round_ids
            )
            if duplicate:
                return self._detail(run)
            if run.session.status != SessionStatus.IN_PROGRESS:
                raise PracticeConflictError("This session is no longer active.")
            if event.kind == "analysis":
                state.analysis_scored = True
                xp = 0  # Analysis is preparation, never an XP-earning activity.
            elif event.kind == "task":
                task = next((row for row in scene.tasks if row.id == event.item_id), None)
                if task is None:
                    raise PracticeConflictError("Unknown task.")
                state.completed_task_ids.append(task.id)
                xp = task.xp
            else:
                if not {row.id for row in scene.tasks} <= set(state.completed_task_ids):
                    raise PracticeConflictError("Finish learning tasks before I-Spy.")
                if event.kind == "round":
                    round = next((row for row in scene.rounds if row.id == event.item_id), None)
                    if round is None or event.answer_id not in {row.id for row in round.choices}:
                        raise PracticeConflictError("Invalid round or answer.")
                    correct = event.answer_id == round.answer_id
                    state.answers[round.id] = event.answer_id
                    state.rounds_played += 1
                    state.correct_rounds += int(correct)
                    xp = 5 if correct else 2
                else:
                    if (
                        not any(row.id == event.item_id for row in scene.prompts)
                        or not (event.text or "").strip()
                    ):
                        raise PracticeConflictError("A valid prompt and clue are required.")
                    xp = 2  # Participation credit; this demo does not evaluate free-form clues.
                    state.clues[event.item_id] = event.text
                state.scored_round_ids.append(key)
            state.session_xp += xp
            progress.xp += xp
            run.session.updated_at = utc_now()
            return self._detail(run)

        return self._attach_objects(self.repository.change(change))

    def complete(self, session_id: UUID) -> Session:
        profile = self._profile()
        progress, initial = self._find(self.repository.read(), session_id, profile)
        scene = self.scenes.get_scene(initial.state.scene_id, progress.language_code)

        def change(rows: list[StoredProgress]) -> Session:
            progress, run = self._find(rows, session_id, profile)
            if run.session.status == SessionStatus.COMPLETED:
                return run.session
            keys = {f"round:{row.id}" for row in scene.rounds} | {
                f"clue:{row.id}" for row in scene.prompts
            }
            if (
                run.session.status != SessionStatus.IN_PROGRESS
                or not {row.id for row in scene.tasks} <= set(run.state.completed_task_ids)
                or not keys <= set(run.state.scored_round_ids)
            ):
                raise PracticeConflictError("Finish the practice before completing this session.")
            run.session.completed_at = utc_now()
            run.session.status = SessionStatus.COMPLETED
            progress.scenarios = [
                row for row in progress.scenarios if row.scene_id != scene.scene_id
            ]
            progress.scenarios.append(
                ScenarioProgress(
                    scene_id=scene.scene_id,
                    status="completed",
                    spoken_items=len(scene.items),
                    total_items=len(scene.items),
                    level=profile.proficiency_level,
                )
            )
            return run.session

        return self.repository.change(change)

    def review_objects(
        self, session_id: UUID, request: ReviewSceneObjectsRequest
    ) -> SessionDetailResponse:
        _, run = self._find(self.repository.read(), session_id)
        assert self.scene_objects is not None
        self.scene_objects.review(session_id, run.session.user_id, request)
        return self.get(session_id)

    def abandon(self, session_id: UUID) -> Session:
        profile = self._profile()

        def change(rows: list[StoredProgress]) -> Session:
            _, run = self._find(rows, session_id, profile)
            if run.session.status == SessionStatus.ABANDONED:
                return run.session
            if run.session.status in {SessionStatus.COMPLETED, SessionStatus.FAILED}:
                raise PracticeConflictError("This session has already ended.")
            run.session.abandoned_at = utc_now()
            run.session.status = SessionStatus.ABANDONED
            run.session.updated_at = utc_now()
            return run.session

        return self.repository.change(change)
