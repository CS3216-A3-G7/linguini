# Linguini backend

FastAPI/Pydantic API with SQLAlchemy persistence in Supabase PostgreSQL. Prisma
owns schema migrations; it is not the Python runtime client. API JSON uses camelCase
and Python attributes use snake_case. See the [project README](../README.md) for the frontend.

## Setup

Use Python 3.12+ and Node/npm. From `backend/` in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm ci
Copy-Item .env.example .env.local
```

Skip creating the environment or copying the environment file if it already exists.
Fill these variables in `backend/.env.local`:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Backend PostgreSQL URI. In Supabase's Connect dialog, copy the direct or **session pooler** connection URI, replace the password, and use `sslmode=require`. Session pooler port is 5432; transaction pooler port 6543 is not supported by this backend. URL-encode special characters in credentials. |
| `DIRECT_URL` | Prisma migration URI: direct connection or session pooler. Use a database role permitted to apply DDL. |
| `DEMO_USER_ID` | UUID of an existing `users` row. The default example UUID must exist in your database to use `/me`. This is temporary demo identity, not authentication. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins, including the port; defaults to `http://localhost:5173`. |

Database URLs stay on the backend. No Supabase anon key, service-role key, or AI
provider key is needed for database access. Do not append Prisma's `pgbouncer=true`
option to a SQLAlchemy connection URI. SQLAlchemy uses the psycopg driver internally.

```powershell
npm run db:validate
npm run db:deploy
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --env-file .env.local
```

On macOS/Linux, use `python3 -m venv .venv`, `.venv/bin/python`, and `cp` instead.
API docs: `http://127.0.0.1:8000/docs`; OpenAPI: `/openapi.json`.
Set frontend `VITE_API_BASE_URL=http://127.0.0.1:8000` without `/api/v1`.
Restart the appropriate server after changing environment settings.

**PostgreSQL is required.** The old `USER_STORAGE`, `LANGUAGE_PROFILE_STORAGE`,
`MEDIA_ASSET_STORAGE`, `VOCABULARY_STORAGE`, `SESSION_STORAGE`, and `JOURNAL_STORAGE`
switches have been removed. Existing values are ignored and can be deleted from
local environment files. Missing database configuration fails at startup; connection
or query failures never fall back to JSON. The application creates one SQLAlchemy
engine per process and disposes it at shutdown.

## Persistence and remaining static content

| Data | Runtime storage |
| --- | --- |
| Users and language profiles | `users`, `language_profiles` |
| Image/audio metadata | `media_assets` (file bytes are not stored here) |
| Vocabulary | `vocabulary_items`, `vocabulary_translations`, `user_vocabulary_progress`, `vocabulary_encounters` |
| Practice | `sessions`, `scene_objects`, `user_practice_progress` |
| Tasks | `session_tasks`, `task_attempts`, `task_hints` |
| Journals | `journals`, `journal_media`, `journal_revisions`, `journal_suggestions`, `journal_word_mentions` |
| AI observability | `ai_generation_runs` |
| Preloaded scene definitions, markers, demo questions and prompts | `preloaded_scenes` |

The scene catalog is read from PostgreSQL through `PostgresSceneRepository`.
`preloaded_scenes` stores a UUID, unique URL slug, language code/display name, title,
description, art key, difficulty, media FK, sort order, active flag and timestamps.
JSONB `content` holds the reusable markers/tasks/rounds/prompts and is validated
against `PreloadedSceneDetail` when reading. Metadata comes from columns,
not arbitrary content keys. The image FK restricts deletion; triggers require a
shared preloaded image and prevent changing referenced media to another source/type.
Inactive scenes are excluded from catalog and detail reads. Existing slugs and the
frontend response contract are preserved. SVG artwork remains in the frontend.

The built-in scene catalog is preserved in the
`20260918090000_seed_preloaded_scenes` migration. Run `npm run db:deploy` to apply it.
It inserts missing media IDs and scene slugs without overwriting existing rows.
This supports fresh installations without a JSON file or an import command.

The legacy `app/import_*.py` tools, JSON fixtures, and file-backed test adapters
have been removed. Existing migrated user data stays in PostgreSQL. Fresh databases
contain the catalog but no demo users or learner history; provision a user and set
`DEMO_USER_ID` to that user's UUID before using the demo API.

Repository interfaces and shared errors remain in `app/repositories/`;
SQLAlchemy implementations live in `app/repositories/postgres/`. Services depend
on these interfaces, while FastAPI dependencies supply PostgreSQL implementations.
They are separate responsibilities rather than duplicate persistence code.

## Behavior and constraints

Users own language profiles; language pairs are unique per user and only one profile
can be active. Switching profiles filters vocabulary and the scene catalog. Name,
learning goal, preferences, level, and daily minutes persist in PostgreSQL. Browser
camera/microphone permissions remain separate from saved preferences.

Vocabulary reads use the active target language and its source-language translation
in one database snapshot. Missing translations remain null. Trusted backend events
use `PostgresVocabularyRepository.record_encounter` to atomically record an event
and update counters. Stable IDs make event retries idempotent; conflicting reuse is
rejected. Mastery/status are not inferred from counters. Composite foreign keys
require every encounter's session to belong to its user, and its task to belong
to that exact session. Missing parents and cross-user/session references are
rejected even for direct SQL writes. These constraints establish ownership and
existence; they do not prove an answer was evaluated or a task was completed.

The `20260918100000_enforce_encounter_parents` migration validates existing history
and fails atomically if invalid references exist. Before deploying it to an existing
database, this query should return no rows:

```sql
SELECT e.id, e.user_id, e.session_id, e.session_task_id
FROM public.vocabulary_encounters e
LEFT JOIN public.sessions s ON s.id = e.session_id AND s.user_id = e.user_id
LEFT JOIN public.session_tasks t ON t.id = e.session_task_id AND t.session_id = e.session_id
WHERE s.id IS NULL OR t.id IS NULL;
```

Reconcile any results with real historical records before deployment; the migration
does not fabricate parents, delete encounters, or adjust counters. Foreign keys use
`NO ACTION`, deferred until transaction commit: individual sessions/tasks cannot be
deleted while referenced, but deleting an entire user's aggregate can cascade
atomically. Prisma records the relations; SQL defines the deferred-check behavior.

Practice sessions and XP update in one transaction. Retrying a scored demo event
awards XP once. Sessions are owned by the user/profile; a new active session can
abandon the prior session for that profile. Normalized task records protect private
answers, attempts, hints, and completion state. The demo frontend still uses the
scene's scripted task payload and `sessions.demo_state`; do not remove that JSONB
column until the frontend uses normalized task APIs throughout.

Journals are unique per user/local date across all target languages. Saves append
immutable revisions, with identical retries avoiding duplicate revisions. Media
must be owned or preloaded images; audio must be owned. Suggestion acceptance
requires the expected base revision and atomically creates a new revision.
Annotation offsets use zero-based Unicode code points with an exclusive end;
JavaScript UTF-16 offsets must be converted for supplementary characters. Child rows
cascade when their journal is deleted; referenced media/vocabulary remain protected.

AI runs record feature, model/prompt/schema versions, pending/succeeded/failed status,
optional nonnegative BIGINT token counts and latency, validation outcome, error code,
and input/output references. Null metrics mean unknown. Composite foreign keys
ensure linked sessions/journals belong to the run's user. Ownerless runs are system
jobs and cannot reference a session or journal. Deleting a linked user/session/journal
also deletes its runs.

Trusted workers use `PostgresAiGenerationRunRepository(engine, user_id)` and
`AiGenerationRunCompletion`. `create` starts a pending run with a stable UUID;
matching retries return its current record. `finish` records succeeded or failed,
with completion time defaulting to current UTC. Failure requires a nonblank error
code. Concurrent completion serializes, identical retries succeed, and conflicting
results are rejected. Identity/version fields and completed results are immutable.
`get` and `list_runs` are owner-scoped; `user_id=None` means system runs only.
Deduplicating run records does not provide a provider-job lease. Store storage
identifiers in input/output references rather than raw prompts.

Tables use UUID identities and timezone-aware timestamps. Migrations define foreign
keys, checks, update triggers, RLS, and revoked browser-role grants. All access is
through backend repositories; the frontend must not query these tables directly.

## Remaining integration work

Authentication, camera uploads/media processing, AI generation and speech evaluation
are not implemented. AI runs are populated only when backend workers call the
repository; ordinary frontend use does not fabricate run records. Vocabulary
"Move" is still local frontend state. Demo scoring is not yet connected to the
vocabulary encounter writer. Daily vocabulary, home aggregation, and other unfinished
routes return an explicit 501. Journal eligible-photo/learned-word recommendations
and automatic annotations remain unpopulated. Creating tables does not implement
these provider or frontend flows.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Without `TEST_DATABASE_URL`, PostgreSQL integration tests are skipped. For complete
coverage, point `TEST_DATABASE_URL` to a **disposable migrated test database** and run
the suite. Integration tests create and delete records; never use a live Supabase
project as the test database. Pure schema/error-handling tests run without a database. Persistence and API tests
use PostgreSQL, create their own records in Python, and clean up after themselves.
Scene tests read the catalog installed by migrations; no test JSON files or alternate
storage adapters are used. The tests exercise the production dependency graph.

Production sources are under `app/`, migrations under `prisma/migrations/`,
and database/schema tests under `tests/`.
