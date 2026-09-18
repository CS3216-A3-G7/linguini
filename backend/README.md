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

Users and language profiles optionally persist in Supabase PostgreSQL; see the setup below.
Authentication, media processing, and AI integrations are not implemented.
Journal services enforce one journal per user/local day.
No API keys or database are required.
The `tzdata` dependency supplies IANA timezone data for the existing User validator
on systems such as Windows that do not provide it.

## Setup

### Vocabulary: catalog, translations, learner progress and encounters

The next migration adds `vocabulary_items`, `vocabulary_translations`,
`user_vocabulary_progress`, and `vocabulary_encounters`. Use the existing database
URLs; no new credentials are required. From `backend/`:

```powershell
npm run db:validate
npm run db:deploy
.\.venv\Scripts\python.exe -m app.import_users
.\.venv\Scripts\python.exe -m app.import_language_profiles
.\.venv\Scripts\python.exe -m app.import_media_assets
.\.venv\Scripts\python.exe -m app.import_vocabulary
```

Then set these in `backend/.env.local` and restart Uvicorn:

```dotenv
USER_STORAGE=postgres
LANGUAGE_PROFILE_STORAGE=postgres
VOCABULARY_STORAGE=postgres
```

`VOCABULARY_STORAGE` defaults to `json`. PostgreSQL mode requires PostgreSQL users
and language profiles so translation selection follows the active source/target pair.
`GET /api/v1/me/vocabulary` keeps its camelCase response and cursor pagination.
It reads the active target language, its translation into the profile's source
language, the current user's progress, and that user's encounter IDs in one database
snapshot. Missing translations remain `null`; another language's translation is not
silently substituted. Scene/topic labels are retained on each saved progress record.
XP, leaderboards and scenario progress continue using `progress.json`.

| Table | Relations and constraints |
| --- | --- |
| `vocabulary_items` | Shared catalog with language, lemma, display text, part of speech, optional grammatical/example metadata and CEFR level. Optional pronunciation FK to `media_assets`; database triggers require audio. Deleting audio clears the reference. |
| `vocabulary_translations` | FK to a catalog item, one primary translation per item/source language (case-insensitive). Item deletion cascades to translations. |
| `user_vocabulary_progress` | FKs to user and item; unique `(user_id, vocabulary_item_id)`. Nonnegative counters with correct attempts <= exposures; exact `DECIMAL(6,5)` mastery score between 0 and 1. User deletion cascades; referenced catalog item deletion is restricted. |
| `vocabulary_encounters` | Composite FK to the user's progress pair, preventing history for an unrelated user/item. Required session/task UUIDs, encounter type, outcome and occurrence timestamp. Progress deletion cascades to history. |

All four tables have UUID primary keys, timezone-aware timestamps, update triggers,
RLS enabled and no browser-role grants. Part-of-speech, status, CEFR, encounter type
and outcome values are checked in PostgreSQL. Language/lemma is indexed but not
unique: homonyms and distinct senses can have separate item IDs. `scene_id` remains
presentation metadata until scenes migrate. Sessions/tasks remain UUID references
without foreign keys until tasks and historical references migrate together; no placeholder session rows are
invented. The active demo user selection is still not authentication.

The importer reads the existing `DailyVocabularyItem[]` JSON, normalizes shared
items/translations, validates references and writes all tables in one transaction.
It preserves IDs/timestamps and skips existing IDs without resetting live progress.
Conflicting IDs in the source fail validation; natural-key or FK conflicts roll back
the whole batch. Import any referenced users and pronunciation media first.

The current fixtures contain no encounters, so the encounter table starts empty.
To migrate real history, supply full `VocabularyEncounter[]` records:

```powershell
.\.venv\Scripts\python.exe -m app.import_vocabulary --path path/to/vocabulary.json --encounters path/to/encounters.json
```

Every `encounterIds` reference in a vocabulary bundle must match a supplied event's
user/item. IDs alone are insufficient to recover session/task IDs, outcome or time.
History imports preserve supplied counter snapshots rather than replaying events.

`PostgresVocabularyRepository.record_encounter()` is for trusted, evaluated backend
events. It creates missing progress and records the event with its counter updates
in a single transaction. It locks the user row to serialize concurrent updates.
Retrying a stable event ID with identical event data does not count twice; reusing
the ID for different data raises a conflict. Each new event increments exposures,
and `correct` outcomes increment correct attempts. First-learned time tracks the
earliest event; last-practised time tracks the latest non-introduction event.
Status and mastery score are intentionally not inferred from these counts.

The demo practice event flow is not connected to this writer yet, and vocabulary
"Move" remains frontend state only. No public endpoint accepts self-reported correct
outcomes. Daily-vocabulary and individual-item routes remain their existing 501
placeholders. This step migrates the tables and existing list read path.

`tests/test_postgres_vocabulary.py` covers validation and, with `TEST_DATABASE_URL`
pointing to a dedicated migrated PostgreSQL database, import replay/rollback,
translation selection, ownership, pagination, concurrency, event idempotency,
constraints, RLS and pronunciation-media integrity.

### Media assets: third PostgreSQL table

`media_assets` stores image/audio **metadata**, not file bytes. It preserves the
existing `MediaAsset` API shape and UUIDs referenced by scenes and practice sessions.
Scene definitions and artwork remain in their existing JSON/frontend locations.

From `backend/`, using the existing database URLs:

```powershell
npm run db:validate
npm run db:deploy
.\.venv\Scripts\python.exe -m app.import_users
.\.venv\Scripts\python.exe -m app.import_media_assets
```

The default importer extracts the six shared assets from `app/data/scenes.json`.
It preserves UUIDs/timestamps, deduplicates identical shared references, and skips
IDs already in PostgreSQL. Conflicting source IDs/keys fail validation; database
key conflicts or missing owners roll back the entire import. It never uploads files
or overwrites existing metadata. To import a flat array of `MediaAsset` objects:

```powershell
.\.venv\Scripts\python.exe -m app.import_media_assets --format assets --path path/to/assets.json
```

After importing, set `USER_STORAGE=postgres` and `MEDIA_ASSET_STORAGE=postgres`
in `backend/.env.local`, then restart the backend. The media switch defaults to
`json`; PostgreSQL media requires PostgreSQL users. No additional credentials are
needed for this metadata migration.

With the switch enabled, scene list/detail responses use PostgreSQL media metadata,
loaded in a batch by the IDs still in scene JSON. Missing or non-preloaded scene
assets produce a controlled storage error instead of falling back to stale JSON.
`GET /api/v1/media/{asset_id}` returns metadata for the current demo user's own
assets or shared preloaded assets. Missing/other-user assets return 404; ownerless
generated assets are not automatically public. JSON mode can look up the embedded
preloaded scene assets. This still uses `DEMO_USER_ID`, not authentication.

| Field | Database decision |
| --- | --- |
| `id` | UUID primary key; imports preserve IDs |
| `owner_user_id` | Nullable FK to users; required for camera/user uploads, absent for preloaded media |
| `media_type`, `source` | Bounded strings with CHECK constraints matching the API enums |
| `storage_key` | Unique nonempty opaque key; use a globally unique namespace, including bucket if multiple buckets are introduced |
| `mime_type` | Required MIME type with an image/audio prefix matching `media_type` |
| `width`, `height` | Optional positive integers; prohibited for audio |
| `duration_ms` | Optional positive integer; prohibited for images |
| `captured_at` | Optional timezone-aware timestamp, distinct from creation time |
| `created_at`, `updated_at` | timestamptz(6), with database-managed update trigger |

Owner deletion is restricted while media rows reference the user. Account deletion
must explicitly clean up files and metadata first; deleting a database row alone
cannot delete an object-storage file. RLS/browser restrictions match the other
tables. Sessions, scene objects and journal attachments will receive foreign keys
to media assets when those tables migrate. Do not add a foreign key to Supabase's
internal `storage.objects` table: demo keys are bundled assets and file lifecycle
belongs to the storage integration.

Signed uploads, storage buckets and file verification are **not implemented** by
this table migration. `/media/upload-url` and `/media/confirm-upload` still return
501; a confirmation must verify a server-issued key, ownership and actual file
metadata before registering an asset. The PostgreSQL repository exposes `create`
for trusted backend code, not an unrestricted public metadata-write endpoint.

`tests/test_media_assets.py` covers schema validation, shared JSON references,
ownership, controlled errors, imports, rollback, scene hydration, FK/check/unique
constraints, RLS enablement and timestamps. Set `TEST_DATABASE_URL` to a dedicated
migrated PostgreSQL test database to run the database cases.

### Language profiles: second PostgreSQL table

Users must be migrated first. From `backend/`, use the existing database credentials:

```powershell
npm run db:validate
npm run db:deploy
.\.venv\Scripts\python.exe -m app.import_users
.\.venv\Scripts\python.exe -m app.import_language_profiles
```

Prisma uses `DIRECT_URL` when set, otherwise `MIGRATION_DATABASE_URL`. Either must
be a direct or session-pooler connection, not port 6543. SQLAlchemy continues using
`DATABASE_URL`. There is no new credential for language profiles.

After the import, set these in `backend/.env.local` and restart Uvicorn:

```dotenv
USER_STORAGE=postgres
LANGUAGE_PROFILE_STORAGE=postgres
```

The new switch defaults to `json`, preserving an existing users-only deployment
until its profiles are imported. PostgreSQL profiles require PostgreSQL users.
Switching back to JSON does not copy database edits back to the source files.

In the frontend `/profile`, selecting a language creates or activates its persisted
profile. Check `public.language_profiles` in Supabase's Table Editor. GET/POST/PATCH
language-profile routes use SQLAlchemy; content filtering and journal context use
the active PostgreSQL profile. Other storage switches control vocabulary and sessions/progress; scene catalogs and journals remain JSON.
This remains demo identity selection, not authentication.

Each profile has a UUID, a required `user_id` foreign key to `users.id`, language
codes up to 35 characters, a CEFR proficiency level, an input preference, an active
flag, an optional daily goal (1–240 minutes), and timezone-aware timestamps.
Levels and input modes use bounded strings with database CHECK constraints matching
the API enums. Language codes retain case, but pair uniqueness and the requirement
for different source/target languages are case-insensitive.

A unique expression index prevents duplicate pairs per user. A partial unique index
allows **at most one** active profile per user; zero is valid and produces the
existing choose-a-language response. Activation locks the parent user and deactivates
the previous profile in the same transaction. A failed insert rolls this back.
Deleting a user cascades to their profiles; other tables' deletion behavior will be
defined when they migrate. RLS and browser-role restrictions match the users table.
The existing timestamp trigger function maintains `updated_at` for both tables.
Keep the SQL-only checks, expression/partial indexes and RLS in future migrations.

The profile import preserves IDs, owners, timestamps and active flags, skips IDs
already present, and never overwrites database preferences. It validates duplicate
IDs/pairs and multiple active profiles before writing. Missing users, conflicting
pairs or active-profile conflicts roll back the whole batch. Import before editing
profiles in PostgreSQL; resolve conflicts explicitly rather than resetting live data.
A custom JSON source can be supplied with `--path`.

`tests/test_postgres_language_profiles.py` covers storage configuration and import
validation. With `TEST_DATABASE_URL` pointing to a dedicated migrated test database,
it also tests API switching, ownership, rollback, repeat imports, concurrent activation,
database constraints and cascading deletion. It never loads `.env.local` itself.
Use a full PostgreSQL server for these tests; embedded database wire adapters may
not support the transaction rollback and concurrent row-lock behavior they exercise.

### Users: Supabase PostgreSQL + Prisma migrations + SQLAlchemy

This is an incremental migration: `USER_STORAGE=json` (the default) keeps the
existing demo working; `USER_STORAGE=postgres` switches only the users repository.
Language profiles have their own switch described above. Remaining repositories
continue using JSON and reference the same application user UUID.
Database failures never silently fall back to JSON.

Prisma owns the database schema and migration history. FastAPI uses SQLAlchemy Core
for queries, transactions, and pooling, with psycopg as its synchronous PostgreSQL
driver. The community [Prisma Python client](https://github.com/RobertCraigie/prisma-client-py)
is archived, so it is not a runtime dependency. The Prisma CLI is pinned to ORM 7;
use `npm ci` and the supplied scripts rather than an unpinned global CLI.
Do not run Alembic or SQLAlchemy `create_all` against this schema.

#### First deployment

1. Install the Python dependencies as below, then run `npm ci` inside `backend/`.
   Use Node 22.12+ (or another Node release supported by the pinned Prisma CLI).
2. Set `DATABASE_URL` and `DIRECT_URL` in `backend/.env.local`.
   Use PostgreSQL connection URIs from Supabase's Connect dialog, not the Supabase
   HTTPS API URL or anon key. Percent-encode special characters in the password.
   Example: `postgresql://USER:PASSWORD@HOST:5432/postgres?sslmode=require`.
   A direct connection requires IPv6 unless your project has IPv4 support; the
   [session pooler](https://supabase.com/docs/guides/database/prisma) supports IPv4.
   Use direct or session-mode connections (port 5432) for this first setup, including
   migrations. Do not use the transaction pooler (port 6543).
3. Keep `USER_STORAGE=json` while running these commands from `backend/`:

   ```powershell
   npm run db:validate
   npm run db:deploy
   .\.venv\Scripts\python.exe -m app.import_users
   npm run db:status
   ```

4. Set `USER_STORAGE=postgres`, then restart Uvicorn using `--env-file .env.local`.
   GET and PATCH `/api/v1/me` now read/write PostgreSQL. `DEMO_USER_ID` must identify
   an imported user. To use JSON again, set `USER_STORAGE=json` and restart;
   subsequent PostgreSQL edits are not copied back to JSON.

Migrations and imports are explicit operations, never automatic application startup
actions. The import validates the whole JSON file, inserts in one transaction, keeps
existing UUIDs/timestamps, and skips IDs already present. Conflicting provider IDs
roll back the import. A custom source can be supplied with `--path path/to/users.json`.
No user creation or deletion API is introduced in this step.

The backend DB role must own the table or have appropriate privileges and BYPASSRLS.
Using the same trusted server-side role for migration and runtime works initially.
RLS is enabled with no browser policies, and anon/authenticated table access is
revoked. Never put the database credentials in frontend environment variables.
This does **not** authenticate FastAPI requests: `/me` still selects `DEMO_USER_ID`,
so the API remains a demo until authentication is implemented.

#### User design

| Field | PostgreSQL type / decision |
| --- | --- |
| `id` | UUID primary key, generated by PostgreSQL for new rows; imports retain existing IDs |
| `auth_provider_id` | Unique nonempty text; preserves current `demo-user` and future provider subjects |
| `display_name` | Nonempty varchar(100) |
| `email` | Nullable varchar(320); contact metadata, not a login key, so not unique |
| `timezone` | Text, default `UTC`; API/import validate IANA timezone names |
| `learning_goal` | varchar(300), default empty string |
| `microphone_enabled`, `camera_enabled` | Boolean preferences, default true; not browser permission grants |
| `onboarding_completed` | Boolean, default false |
| `created_at`, `updated_at` | timestamptz(6); database trigger maintains update time |

`users` is the application profile table, separate from Supabase `auth.users`.
There is deliberately no auth foreign key yet: the existing demo identity is not
a Supabase Auth account. When adding Supabase Auth, introduce a nullable unique
`auth_user_id UUID` referencing `auth.users(id)` and link real accounts explicitly;
keep the application UUID stable. Define account deletion behavior in that migration.
Language profiles now reference `users.id`. Future journals, sessions, and progress rows should reference
`users.id` with foreign keys when each table migrates. We cannot enforce foreign keys
to data that still lives in JSON. Learning progress and language preferences belong
in those tables rather than additional JSON columns on users.

The Prisma model describes columns and indexes; the checked-in SQL additionally
owns checks, the timestamp trigger, and RLS. Preserve these in future migrations.
Use `db:dev` only against a disposable development database with shadow-database
permissions; apply reviewed migrations to Supabase with `db:deploy`.

For database integration checks, apply the migrations to a **dedicated test database**,
set `TEST_DATABASE_URL` to its connection URI, and run pytest. The database test
creates and removes its own user and verifies imports, PATCH persistence, timestamps,
and the unchanged API contract. Without that variable, the live test is skipped.

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

Vocabulary Move still changes frontend state only. Practice XP uses JSON by default or PostgreSQL with `SESSION_STORAGE=postgres`.

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
exclusion, and discriminated attempt inputs. PostgreSQL integration tests additionally exercise persistence and database constraints. User tests cover JSON validation and read errors,
service lookup, the complete current-user response, missing users, controlled
storage errors, and allowed/disallowed CORS origins. Frontend checks are
`npm run build` (including TypeScript) and `npm run lint`; no frontend test or
formatter script is configured.

`tests/test_learning.py` also covers the migrated progress/vocabulary data, user
isolation, pagination, invalid cursors, empty results, missing users, controlled
storage errors, and the remaining unimplemented vocabulary endpoints.

## PostgreSQL sessions and scene objects

The session migration adds `sessions`, `scene_objects`, and a transitional
`user_practice_progress` table. The progress table keeps session events and earned
XP in the same transaction. Demo answers and scenario summaries remain JSONB
alongside the normalized task storage. Scene catalog content remains in `scenes.json`.

From `backend/`, with the existing database URLs configured in `.env.local`:

```powershell
npm run db:deploy
python -m app.import_users
python -m app.import_language_profiles
python -m app.import_media_assets
python -m app.import_vocabulary
python -m app.import_sessions
```

Set these switches in `backend/.env.local`, then restart the backend:

```dotenv
USER_STORAGE=postgres
LANGUAGE_PROFILE_STORAGE=postgres
MEDIA_ASSET_STORAGE=postgres
SESSION_STORAGE=postgres
```

`VOCABULARY_STORAGE=postgres` is independently optional. No additional credentials
are needed. Start a practice session in the frontend to populate `sessions`;
practice events update its `demo_state` and `user_practice_progress.xp` atomically.
Repeated create requests with the same key and concurrent duplicate scoring events
do not create duplicate sessions or award XP twice. Starting another session for
the same profile abandons the previous in-progress session.

Scene objects have a session/media composite foreign key, normalized bounding-box
coordinates, confidence, review status, and an optional vocabulary-item reference.
Session ownership must match its language profile, and its media must be an owned
or preloaded image. These rules are checked in PostgreSQL. All three tables enable
RLS and revoke browser-role access; access continues through the backend.

`PATCH /api/v1/sessions/{id}/scene-objects` saves reviews atomically; session reads
include saved objects. `POST /api/v1/sessions/{id}/abandon` is implemented too.
Automatic object detection is not yet implemented, so demo practice does not
invent scene-object rows. A trusted detector can use `PostgresSceneObjectRepository.create`,
or import an array of `SceneObject` records (camelCase API fields):

```powershell
python -m app.import_sessions --scene-objects path/to/scene_objects.json
```

Import sessions before using the PostgreSQL practice flow. The importer skips
existing user/language progress groups **and their sessions** to preserve live XP;
existing scene-object IDs are also left unchanged. Invalid references roll back
the whole import. Import vocabulary first when objects reference vocabulary IDs.
Keep JSON files for the remaining demo catalogs and as migration input.

Encounter-to-session/task foreign keys remain deferred until historical encounter
references are reconciled. Normalized task storage is described below; generated
plans and session summaries remain outside this step.

`tests/test_postgres_sessions.py` exercises PostgreSQL persistence, concurrent
scoring, review rollback, completion, abandonment, and repeatable imports. Set
`TEST_DATABASE_URL` to a disposable migrated PostgreSQL database to run them.

## PostgreSQL tasks, attempts, and hints

The next migration adds `session_tasks`, `task_attempts`, and `task_hints`.
Apply it from `backend/`:

```powershell
npm run db:deploy
```

Task storage uses the existing `SESSION_STORAGE=postgres` setting and database URLs;
there is no additional environment variable. PostgreSQL users, language profiles,
media assets, and sessions must already be enabled and imported.

| Table | Fields and relationships |
| --- | --- |
| `session_tasks` | UUID identity; required session FK; phase, kind, status; globally unique order within the session; public content and private answer key as separate JSONB columns; optional vocabulary FK and scene-object FK constrained to the same session; lifecycle timestamps and skip reason. |
| `task_attempts` | Required task FK; unique positive attempt number per task; input mode and response JSONB; optional correctness, decimal score from 0–1, feedback and private evaluation details; owned audio FK required for speech. |
| `task_hints` | Required task FK; unique positive hint level per task; JSONB content and requested timestamp. |

All entities retain `created_at` and database-managed `updated_at`. Deleting a
session cascades to its tasks, attempts, and hints. Referenced vocabulary and audio
cannot be deleted while task records use them. Table checks enforce content-kind
agreement, valid phase/kind combinations, terminal timestamps, and speech/audio
consistency. RLS is enabled and browser roles have no table access.

`PostgresTaskRepository` provides owner-scoped reads and trusted
`create_task`, `create_attempt`, and `create_hint` writes. Writers supply stable
entity UUIDs and attempt numbers/hint levels; retries of identical records are
idempotent. Conflicting IDs or positions return a conflict instead of overwriting
history. New records cannot be added to terminal sessions, or attempts/hints to
terminal tasks. Historical imports can include terminal records.

`GET /api/v1/tasks/{id}`, `GET /api/v1/sessions/{id}/tasks`, and session details
now expose saved tasks in order. Session details include task counts and the next
unfinished task ID. Public responses omit answer keys. Attempt evaluation details
are available only through the internal repository; no attempt-history endpoint
is exposed by this change.

To import trusted task records, supply a bundle of the existing camelCase entity
schemas. Each array is optional:

```json
{"tasks": [], "attempts": [], "hints": []}
```

```powershell
python -m app.import_tasks --path path/to/tasks.json
```

Import parent sessions, scene objects, vocabulary, and attempt audio first. The
import validates the whole bundle and inserts tasks before attempts and hints in
one transaction. Existing IDs are preserved; reusing an ID under a different
parent is rejected. Any invalid record rolls back all new records in that import.

The demo scene task definitions use string IDs and a different content schema;
they are not automatically converted into `SessionTask` entities. Generated task
planning, grading, hint generation, and task action endpoints remain unimplemented
(501). This step provides persistence and read APIs, without inventing grading
results or awarding additional demo XP. Public-content JSONB is a content snapshot;
only the explicit relational columns carry database foreign keys. Existing
vocabulary encounter UUIDs still require reconciliation before adding their
session/task foreign keys.

`tests/test_postgres_tasks.py` covers persistence, public-answer exclusion,
ownership, ordering conflicts, speech media, state constraints, imports, rollback,
RLS configuration, and cascade deletion. Set `TEST_DATABASE_URL` to a disposable
database with all migrations applied before running these tests.

## PostgreSQL journals

The journal migration adds five tables and connects the existing frontend save,
edit, history, and revision routes to SQLAlchemy:

| Table | Fields and constraints |
| --- | --- |
| `journals` | UUID identity, owner/profile composite FK, local date and timezone, title/art/selected words, draft/completed state, current revision, optional owned audio. Unique `(user_id, local_date)` applies across all target languages. |
| `journal_media` | Journal/image FKs, display order, optional caption. Each asset and display position is unique within its journal. Photos must be owned or preloaded images. |
| `journal_revisions` | Journal FK, positive revision number, content up to 20,000 characters, creator. Revision numbers are unique per journal and history cannot be edited in place. |
| `journal_suggestions` | Composite FK ties the base revision to its journal. Stores type, original/replacement text, explanation, offsets and review status. |
| `journal_word_mentions` | Revision and vocabulary FKs, text offsets, matched text, match method and optional source encounter. Source encounters must match the journal owner and vocabulary item. |

All tables have creation/update timestamps, RLS, and revoked browser-role grants.
The current-revision FK is checked at transaction commit, so a journal and its
first revision can be created atomically. Journal deletion cascades to child rows;
referenced media, vocabulary, and source encounters remain protected from deletion
while referenced. Text offsets use **zero-based Unicode code points**, with an
exclusive end; JavaScript callers must convert UTF-16 offsets for emoji and other
supplementary characters. Annotation text must match that exact revision slice.

From `backend/`, using the existing database URLs:

```powershell
npm run db:deploy
python -m app.import_journals
```

Import users and language profiles first, plus media/vocabulary/encounters when
journal records reference them. The default source is `app/data/journals.json`,
an array of `JournalDetailResponse` records containing `journal`, `media`,
`revisions`, `suggestions`, and `wordMentions`. A custom source uses `--path`.
The whole import is atomic. Existing journal IDs and all of their child records
are skipped to preserve live edits. A different ID for the same user/date is a
conflict; no existing journal is overwritten or silently merged.

Then set these in `backend/.env.local` and restart:

```dotenv
USER_STORAGE=postgres
LANGUAGE_PROFILE_STORAGE=postgres
MEDIA_ASSET_STORAGE=postgres
JOURNAL_STORAGE=postgres
```

`JOURNAL_STORAGE` defaults to `json`. It is independent of the session and
vocabulary storage switches; any referenced vocabulary must nevertheless exist
in PostgreSQL. Saving from the frontend now populates `journals` and
`journal_revisions`. Concurrent saves serialize per user, preventing duplicate
daily journals and revision numbers. Repeating the current content does not
create another revision. Switching storage back does not copy database edits
back to JSON.

Additional implemented routes:

- `POST /journals/{id}/media` and `DELETE /journals/{id}/media/{asset_id}` attach
  and detach photos; deleting a link does not delete the media asset.
- `POST /journals/{id}/complete` validates the requested revision and marks the
  journal completed. Journals remain editable through new revisions.
- `POST /journal-suggestions/{id}/accept` applies a stored suggestion as a new
  merged revision atomically. Repeating the acceptance does not duplicate it.
  Suggestions based on an older current revision return 409.
- `POST /journal-suggestions/{id}/reject` records rejection without changing text.

All paths use the `/api/v1` prefix. Journal detail reads include all five entity
types. Trusted feedback/word-matching workers can append validated suggestions and
mentions through `PostgresJournalRepository.change`; history is preserved and the
entire change rolls back on invalid references. AI suggestion generation and
automatic word matching remain unimplemented. The frontend's `selectedWords`
strings are presentation metadata, not fabricated vocabulary mentions. Today's
eligible-photo and learned-word recommendation lists remain unpopulated.

`tests/test_postgres_journals.py` covers concurrent saves, revision history,
completion, media, Unicode annotations, suggestion review, imports, rollback,
ownership, RLS configuration, and deletion. Run with `TEST_DATABASE_URL` pointing
to a disposable PostgreSQL database with all migrations applied.

## AI generation runs

The `ai_generation_runs` table records model and prompt/schema versions, feature,
status, optional latency/token counts, validation outcome, error code, and input/
output references. IDs are UUIDs; timestamps include timezones. Token counts use
nonnegative `BIGINT` values, with `NULL` meaning unknown rather than zero.

Runs can belong to a user and optionally their session and/or journal. Composite
foreign keys enforce ownership. Runs without an owner are reserved for system
jobs and cannot reference a session or journal. Deleting a linked user, session,
or journal cascades to its runs. RLS is enabled and browser-role grants are revoked.

Apply the migration from `backend/`:

```powershell
npm run db:deploy
```

No new environment variables or AI provider keys are needed. This uses the existing
database URLs. The application's database engine is available when
`USER_STORAGE=postgres`. There is no JSON adapter or separate AI storage switch.

Trusted backend workers use `PostgresAiGenerationRunRepository(engine, user_id)`
from `app.repositories.implementations.postgres.ai`. Its `create` method accepts
an `AiGenerationRun` in the `pending` state. Reuse the same UUID for retries:
matching requests return the stored run, including an already completed result.
This deduplicates database records; it does not provide a provider-job lease.
`get` and `list_runs` are scoped to the repository's owner; `user_id=None` reads
only system runs, never all users' runs.

Call `finish(run_id, AiGenerationRunCompletion(...))` to record `succeeded` or
`failed`, optional metrics, and an output reference. Completion time defaults to
the current UTC time. Failure requires a nonblank error code. Concurrent finishes
serialize: identical retries succeed, conflicting results are rejected. Identity
and version fields cannot change, and completed results cannot be overwritten.
Use input/output references for storage identifiers rather than raw prompts.

Historical records can be imported from an explicit JSON array of
`AiGenerationRun` objects after their referenced users, sessions, and journals:

```powershell
python -m app.import_ai_generation_runs --path path/to/ai_runs.json
```

The import is atomic, rejects duplicate source IDs and conflicting identities,
and preserves existing live results. No AI calls or frontend events automatically
create runs yet; the provider integration must call this repository. There are
no public endpoints for writing these internal records.

`tests/test_ai_generation_runs.py` covers lifecycle validation, concurrent writes,
ownership, system runs, database constraints, RLS configuration, and imports.

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
