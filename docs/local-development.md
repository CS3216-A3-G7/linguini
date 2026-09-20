# Local development

## Prerequisites

- Node.js 22.12+ or Node.js 24, with npm.
- Python 3.12 or newer.
- PostgreSQL 16 or another PostgreSQL version supported by the project.
- Docker, if using the throwaway local database described below.

The commands in this guide use macOS/Linux syntax. On Windows, use the
PowerShell equivalents in the repository READMEs, such as
`Copy-Item .env.example .env.local` and `.venv\Scripts\python.exe`.

## Frontend

```sh
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

The Vite development server serves `http://localhost:5173`. Set
`VITE_API_BASE_URL` to the backend origin, without `/api/v1`.

## Backend

Create an isolated environment in `backend/`, install the package, and copy the
environment template:

```sh
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
cp .env.example .env.local
```

Fill in the database and runtime settings in `.env.local`, then validate and
deploy the Prisma migrations:

```sh
npm ci
npm run db:validate
npm run db:deploy
.venv/bin/python -m uvicorn app.main:app --reload --env-file .env.local
```

The API is available at `http://127.0.0.1:8000`; interactive documentation is
at `/docs` and the OpenAPI document is at `/openapi.json`.

### Environment variables

Backend variables are read from `backend/.env.local`:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy/psycopg PostgreSQL connection URI. Use a direct connection or Supabase session pooler on port 5432. |
| `DIRECT_URL` | Prisma migration connection URI with a role allowed to apply DDL. |
| `DEMO_USER_ID` | UUID of an existing `users` row used by the temporary demo identity. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated frontend origins, including their ports. |
| `MEDIA_STORAGE_PRIVATE` | Enables private Supabase Storage signing when `true`. |
| `SUPABASE_URL` | Supabase project URL used by the backend storage adapter. |
| `MEDIA_STORAGE_BUCKET` | Storage bucket name, normally `media-assets`. |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend-only key for Storage operations. Never expose it to the frontend. |
| `MEDIA_PUBLIC_BASE_URL` | Public Storage object base URL when using public media URLs. |

The backend does not support Supabase's transaction pooler on port 6543.
Do not add Prisma's `pgbouncer=true` parameter to the SQLAlchemy URL. Never put
the service-role key in a `VITE_*` variable.

The frontend template contains:

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Backend origin, for example `http://127.0.0.1:8000`, without `/api/v1`. |

## Documentation site

This site needs no database and no Supabase credentials. From the repository
root:

```sh
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r docs/requirements.txt
.venv-docs/bin/mkdocs serve
```

The site is served at `http://127.0.0.1:8000/linguini/`, with live reload on
every saved Markdown change. Pass `-a 127.0.0.1:8001` if the backend already
occupies port 8000. `mkdocs build --strict` produces the static site in `site/`
and is what CI runs.

## Without Supabase: throwaway local PostgreSQL

For local migration and backend-test work, a disposable PostgreSQL container is
enough:

```sh
docker run -d --name linguini-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=linguini_test \
  -p 5432:5432 \
  postgres:16
```

Set all three application/test URLs to this exact local URL:

```text
DATABASE_URL=DIRECT_URL=TEST_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/linguini_test?sslmode=disable
```

In a shell, assign them individually:

```sh
export DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5432/linguini_test?sslmode=disable'
export DIRECT_URL="$DATABASE_URL"
export TEST_DATABASE_URL="$DATABASE_URL"
```

After `backend/npm ci`, apply the schema:

```sh
cd backend
npm run db:deploy
```

The migrations create schema and seeded preloaded scenes, but not a demo user.
On a fresh database, insert a user whose ID matches `DEMO_USER_ID` before using
`/api/v1/me`:

```sql
INSERT INTO users (id, auth_provider_id, display_name, email)
VALUES (
  '11111111-1111-4111-8111-111111111111',
  'local-demo-user',
  'Local Demo',
  'local@example.test'
);
```

Then set `DEMO_USER_ID=11111111-1111-4111-8111-111111111111`.
This local setup does not provide Supabase Storage; storage-backed upload and
signing endpoints still need the backend Supabase variables.
