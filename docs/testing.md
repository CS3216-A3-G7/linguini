# Testing

## Frontend

```sh
cd frontend
npm ci
npm run lint
npm run build
npm run test
```

The test script uses Node's test runner with TypeScript stripping. The build
also runs the TypeScript project build.

## Landing

```sh
cd landing
npm ci
npm run lint
npm run build
```

## Backend

```sh
cd backend
python3 -m pip install -e ".[dev]"
ruff check .
pytest -q
```

PostgreSQL integration tests use `TEST_DATABASE_URL` and skip when it is
unset. The integration files include `test_postgres_users.py`,
`test_postgres_language_profiles.py`, `test_postgres_scenes.py`,
`test_postgres_sessions.py`, `test_postgres_tasks.py`,
`test_postgres_vocabulary.py`, and `test_postgres_journals.py`, plus
database-backed API/read paths. Use a disposable migrated database, never a
live Supabase project:

```sh
TEST_DATABASE_URL="$DATABASE_URL" DATABASE_URL="$DATABASE_URL" pytest -q
```

AI and schema tests use fake clients, demo settings, and deterministic seams.
Evaluation tests are `test_scene_analysis_evals.py` and
`test_scene_translation_evals.py`; they exercise labelled cases and production
validators without requiring a live provider.

## Documentation

From the repository root, in the documentation virtual environment described
in [local development](local-development.md):

```sh
NO_MKDOCS_2_WARNING=true .venv-docs/bin/mkdocs build --strict
```

## CI

`.github/workflows/ci.yml` has six jobs:

| Job | Checks |
| --- | --- |
| `attribution` | Rejects agent/AI attribution in PR commits and descriptions. |
| `frontend` | Node 24 install, lint, build, and test. |
| `landing` | Node 24 install, lint, and Next.js build. |
| `database` | PostgreSQL 16, Prisma validate/deploy/status. |
| `backend` | PostgreSQL 16, migrations, Ruff, and pytest. |
| `docs` | Pinned MkDocs install and strict build. |

`database` and `backend` each provision an isolated PostgreSQL service
container. `docs.yml` separately deploys a Pages artifact on pushes to `main`.

Commits and PR descriptions must not contain `Co-Authored-By`, “Generated
with”, or other AI/agent attribution. Preserve the configured human Git
identity.
