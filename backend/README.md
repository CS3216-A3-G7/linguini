# Linguini backend

FastAPI/Pydantic v2 API contract skeleton for Linguini. See the
[repository README](../README.md) for the frontend and overall project layout.

## Current status

- Versioned `/api/v1` routes cover health, users, home, media, sessions, tasks,
  vocabulary, and journals.
- Pydantic schemas describe language profiles, scene objects, learning tasks,
  I-Spy attempts, journal revisions and suggestions, and AI observability data.
- API JSON uses camelCase; Python attributes use snake_case.
- Validators cover normalized bounding boxes, task content, attempt input modes,
  and completion-state requirements. Public task responses exclude private answers.

`GET /api/v1/health` returns `{"status":"ok"}`. `GET /api/v1/me` returns the existing
`User` model from `app/data/users.json` through route → service → repository.
`GET /api/v1/me/progress` loads XP, scenario progress, and leaderboard data.
`GET /api/v1/me/vocabulary` loads the saved vocabulary list using the existing
`CursorPage[DailyVocabularyItem]` contract. `GET /api/v1/preloaded-scenes` and
`GET /api/v1/preloaded-scenes/{scene_id}` provide scene summaries and details.
Profile, demo-session, and journal persistence are described below. Remaining handlers raise
`501 Not Implemented` with error code `service_not_implemented` when reached;
invalid requests can still receive FastAPI validation errors first.

Authentication, database persistence, media processing, and AI
integrations are not implemented. Journal services enforce one journal per user/local day.
No API keys or database are required.
The `tzdata` dependency supplies IANA timezone data for the existing User validator
on systems such as Windows that do not provide it.

## Setup

Python 3.12 or newer is required. Start from the repository root.
If `backend/.venv` already exists, skip the environment creation command.

### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env.local
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --env-file .env.local
```

These commands use the virtual environment directly, so activation is optional.
To activate it, run `.\.venv\Scripts\Activate.ps1`; then `python` refers to that
environment for the rest of the terminal session.

### macOS / Linux

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
cp .env.example .env.local
python -m uvicorn app.main:app --reload --env-file .env.local
```

The editable install uses `backend/pyproject.toml` and includes the `dev` extra
(HTTPX, pytest, and Ruff). Hatch explicitly packages the `app/` directory.
Run these commands inside `backend/`, where the project configuration lives.

## Local API

| URL | Purpose |
| --- | --- |
| `http://127.0.0.1:8000/api/v1/health` | Health check |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc API reference |
| `http://127.0.0.1:8000/openapi.json` | Generated OpenAPI schema |

In another terminal, run `cd frontend` from the repository root, install with
`npm ci`, copy `.env.example` to `.env.local`, and run `npm run dev`.
Open `http://localhost:5173/home`; the greeting requests `/api/v1/me`.

| Variable | Location | Default / purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `frontend/.env.local` | `http://127.0.0.1:8000`, server origin without `/api/v1`; restart Vite after changes |
| `CORS_ALLOWED_ORIGINS` | `backend/.env.local` | `http://localhost:5173`, comma-separated exact browser origins; restart backend after changes |
| `DEMO_USER_ID` | `backend/.env.local` | `11111111-1111-4111-8111-111111111111`, UUID of the demo user |

Backend defaults work without an env file. The CLI `--env-file .env.local` loads
the example configuration when copied. If Vite uses another port or host, add its
exact origin to `CORS_ALLOWED_ORIGINS`. The JSON path is resolved relative to the
backend module, independent of the working directory. This is a temporary demo
lookup, not authentication. A missing user returns `404` (`user_not_found`);
unreadable, malformed, or schema-invalid JSON returns a controlled `500`
(`user_storage_error`).

## Progress and vocabulary

`app/data/progress.json` is an array of user-scoped progress snapshots.
`app/data/vocabulary.json` is an array of existing `DailyVocabularyItem` models:
each record contains a vocabulary item, translation, learner progress, and optional
`sceneId`/`topic` metadata for the screen. The migrated demo has 12 words, three
scenario-progress records, five leaderboard rows, and 1280 starting XP.

The route calls `LearningService` through FastAPI dependencies, then the
`LearningRepository` interface and `JsonLearningRepository`. The configured user
is checked before lookup. Vocabulary is filtered by its progress `userId`; progress
snapshots are selected by `userId`. The current learner's leaderboard name comes
from the existing user service. No database or authentication was added.

Vocabulary accepts `limit` (1–100, default 50) and the previous response's
`nextCursor`. Pass that cursor unchanged to fetch the next page; `nextCursor: null`
marks the end. Invalid cursors return 400. Empty vocabulary returns an empty page;
missing progress returns 404. Invalid JSON, invalid model data, and file read errors
return a controlled 500. Daily vocabulary and individual-word GET routes remain 501.

Start both apps using the setup commands above and open
`http://localhost:5173/progress` or `http://localhost:5173/vocabulary`. If port 8000
is occupied, start Uvicorn with `--port 8001` and set the frontend's
`VITE_API_BASE_URL=http://127.0.0.1:8001`. CORS still allows the frontend origin
`http://localhost:5173`. Reload the browser after changing demo JSON.

Vocabulary Move still changes frontend state only. Practice XP is saved to JSON.

### Persisted demo practice and journals

Practice routes use `PracticeService` and `JsonPracticeRepository`. Session state
and XP are written together to `app/data/progress.json`, under the user's language
row, using the shared atomic JSON store. Create/resume/read/complete reuse the
existing session routes. `POST /api/v1/sessions/{id}/demo-events` accepts an analysis,
task, multiple-choice round, or clue event. It validates IDs against the scene,
calculates XP on the server, and awards each action once per session, including
concurrent retries. `demoState` on the existing session detail response restores
the frontend. Create requests support the existing `idempotencyKey` field.

`JournalService` and `JsonJournalRepository` use `app/data/journals.json` for journal
metadata and revisions. Implemented routes: `GET /journals`, `GET /journal/today/context`,
`PUT /journal/today`, `GET/PATCH /journals/{id}`, and `POST /journals/{id}/revisions`
(all under `/api/v1`). Reads and edits check demo-user ownership. Daily creation
uses the user's timezone and active profile. History includes all of their languages.
Missing records return 404, conflicting actions 409, invalid input 422, and invalid
JSON or failed file writes a controlled 500. Repeated identical content is idempotent.

Run a single backend worker with the existing environment setup. No database,
authentication, or additional environment variables are introduced. Demo answers
remain visible in scene fixtures; free-form clues earn participation credit only.
AI/media processing and unrelated placeholder routes remain unimplemented.
`tests/test_persistence.py` covers reloads, concurrent duplicate events, scoring,
completion, isolation, failed writes, journal revisions, and CORS for writes.

## Checks

### Persisted user and language profiles

The existing `PATCH /api/v1/me` and language-profile GET/POST/PATCH endpoints now
use services and JSON repositories. `users.json` also stores `learningGoal`,
`microphoneEnabled`, and `cameraEnabled`; omitted fields retain their values.
`language_profiles.json` holds each user's language pair, active flag, level,
input preference, and daily minutes. New profiles become active; activating one
deactivates only that user's other profiles in the same atomic file update.
Duplicate language pairs return 409, unknown/other-user profile IDs return 404,
and invalid request values return 422. Explicit null daily minutes clears the goal.

Scene catalog/detail, vocabulary, and progress requests resolve the configured
user's active target language. Scene and progress JSON now include `languageCode`;
vocabulary already includes it. No active profile returns 409 with instructions
to choose one. The supplied content is Spanish-only; other active languages return
empty content, and mismatched scene-detail requests return 404. User and language
selection remain demo identity selection via `DEMO_USER_ID`, not authentication.

JSON writes validate data, hold a process-wide lock across read/modify/write, and
replace the file atomically. Run a single backend worker. Onboarding uses separate
user and language-profile writes; they are not a cross-file transaction. A failure
is visible and can be retried. Malformed/unreadable storage and failed writes return
controlled 500 errors without overwriting the original file on a failed replacement.
Tests in `tests/test_language_profiles.py` exercise switching, persistence,
cross-user isolation, one-active-profile enforcement, validation, and failure recovery.

CORS now permits GET, POST, PATCH, PUT, and the Content-Type request header. Existing
startup/environment commands are unchanged. To verify, choose French in `/profile`,
reload, check empty `/practice` and `/vocabulary`, then switch back to Spanish.

Scene data lives in `app/data/scenes.json`, containing the six migrated demo scenes.
The existing `PreloadedScene` catalog model now includes `sceneId`, `art`, and
`language`; its existing media metadata, title, description, and difficulty fields
are retained. Details extend that model with typed demo items, tasks, rounds, and
prompts. These are static demo content, separate from live `SessionTaskPublic`
contracts. Demo answers remain client-visible to preserve the current practice
flow; live AI evaluation is still unimplemented. Demo sessions now persist.

Routes call `SceneService` through FastAPI dependencies and the `SceneRepository`
interface, backed by `JsonSceneRepository`. The repository validates IDs, item
references, and marker coordinates. An empty JSON array produces an empty catalog;
unknown scene slugs return 404; invalid or unreadable storage produces a controlled
500. `mediaAsset.storageKey` values such as `demo-art/street` identify bundled SVG
artwork; they are not upload URLs. Frontend artwork still renders locally.

Use the same local startup commands and API/CORS environment variables as above.
Visit `/practice` or `/practice/calle-mayor/analysis` in the frontend. Tests in
`tests/test_scenes.py` cover catalog/detail contracts, migrated content, missing
scenes, empty data, bad JSON, invalid references, duplicate IDs, and CORS.

From `backend/` on Windows, without activating the environment:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m ruff format --check app/config.py app/api/dependencies.py app/repositories app/services tests/test_users.py
```

With the virtual environment activated on any platform:

```sh
python -m pytest
python -m ruff check .
python -m ruff format --check app/config.py app/api/dependencies.py app/repositories app/services tests/test_users.py
```

Tests cover the health response, core OpenAPI paths, explicit unimplemented-service
errors, camelCase serialization, bounding boxes, task content, private-answer
exclusion, and discriminated attempt inputs. They do not test end-to-end learning
flows or database behavior. User tests cover JSON validation and read errors,
service lookup, the complete current-user response, missing users, controlled
storage errors, and allowed/disallowed CORS origins. Frontend checks are
`npm run build` (including TypeScript) and `npm run lint`; no frontend test or
formatter script is configured.

`tests/test_learning.py` also covers the migrated progress/vocabulary data, user
isolation, pagination, invalid cursors, empty results, missing users, controlled
storage errors, and the remaining unimplemented vocabulary endpoints.

## Layout

```text
backend/
|-- app/
|   |-- main.py           FastAPI app factory and application instance
|   |-- api/
|   |   |-- router.py     Versioned router assembly
|   |   |-- errors.py     Shared unimplemented-service error
|   |   `-- routes/       Route contracts grouped by feature
|   `-- schemas/          Pydantic models and validation
|-- tests/
|   |-- test_openapi.py   Health and API contract checks
|   `-- test_schemas.py   Model validation and serialization checks
|-- .gitignore           Virtual environment and Python cache exclusions
|-- pyproject.toml       Build, dependencies, pytest, and Ruff configuration
`-- README.md
```

User domain logic lives in `app/services/users.py`, its repository interface in
`app/repositories/users.py`, and the JSON adapter in
`app/repositories/implementations/json/users.py`. FastAPI dependencies in
`app/api/dependencies.py` wire these together. `app/config.py` reads demo/CORS
environment settings; `app/data/users.json` contains the single demo user.
