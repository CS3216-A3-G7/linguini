from uuid import UUID

from app.repositories.practice import PracticeRepository
from app.schemas.base import utc_now
from app.schemas.enums import SessionStatus
from app.schemas.progress import ScenarioProgress, StoredProgress
from app.schemas.sessions import (
    CreateSessionRequest,
    DemoPracticeEventRequest,
    DemoPracticeState,
    Session,
    SessionDetailResponse,
    StoredDemoSession,
)
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
    ) -> None:
        self.repository = repository
        self.users = users
        self.profiles = profiles
        self.scenes = scenes

    def _profile(self):
        self.profiles.active_language()
        return next(row for row in self.profiles.list_profiles() if row.is_active)

    @staticmethod
    def _detail(run: StoredDemoSession) -> SessionDetailResponse:
        return SessionDetailResponse(session=run.session, demo_state=run.state)

    def _find(self, rows: list[StoredProgress], session_id: UUID):
        profile = self._profile()
        for progress in rows:
            if progress.user_id != profile.user_id:
                continue
            for run in progress.practice_sessions:
                if run.session.id == session_id and run.session.language_profile_id == profile.id:
                    return progress, run
        raise PracticeNotFoundError("Session not found for the active language.")

    def get(self, session_id: UUID) -> SessionDetailResponse:
        _, run = self._find(self.repository.read(), session_id)
        return self._detail(run)

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
        return self._detail(runs[-1]) if runs else None

    def create(self, request: CreateSessionRequest) -> SessionDetailResponse:
        profile = self._profile()
        if request.language_profile_id != profile.id:
            raise PracticeConflictError("Select the active language profile.")
        scene = next(
            (
                row
                for row in self.scenes.list_scenes(profile.target_language_code)
                if row.media_asset.id == request.media_asset_id
            ),
            None,
        )
        if scene is None:
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
                if request.idempotency_key and run.idempotency_key == request.idempotency_key:
                    if run.session.scene_media_asset_id != request.media_asset_id:
                        raise PracticeConflictError(
                            "Idempotency key already used for another scene."
                        )
                    return self._detail(run)
            for previous in progress.practice_sessions:
                if previous.session.status == SessionStatus.IN_PROGRESS:
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
                state=DemoPracticeState(scene_id=scene.scene_id),
                idempotency_key=request.idempotency_key,
            )
            progress.practice_sessions.append(run)
            return self._detail(run)

        return self.repository.change(change)

    def record(self, session_id: UUID, event: DemoPracticeEventRequest) -> SessionDetailResponse:
        def change(rows: list[StoredProgress]) -> SessionDetailResponse:
            progress, run = self._find(rows, session_id)
            scene = self.scenes.get_scene(run.state.scene_id, progress.language_code)
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
                xp = 12
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

        return self.repository.change(change)

    def complete(self, session_id: UUID) -> Session:
        def change(rows: list[StoredProgress]) -> Session:
            progress, run = self._find(rows, session_id)
            if run.session.status == SessionStatus.COMPLETED:
                return run.session
            scene = self.scenes.get_scene(run.state.scene_id, progress.language_code)
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
                    level=self._profile().proficiency_level,
                )
            )
            return run.session

        return self.repository.change(change)
