# Local development

## Prerequisites

- Node.js 22.12 or newer (Node 24 is used in CI) and npm.
- Python 3.12 or newer.
- PostgreSQL 16, or Docker for the throwaway container below.
- Supabase credentials for authenticated production-like runs and
  Storage-backed media. PostgreSQL-only work does not need them.

Commands use macOS/Linux syntax. On Windows, use the PowerShell equivalents
from the repository instructions.

## Frontend

```sh
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Vite serves `http://127.0.0.1:5173`. `VITE_API_BASE_URL` is the backend origin
without `/api/v1`. The browser Supabase client uses the publishable
`VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`; never expose a service-role
key in a `VITE_*` variable.

## Backend

```sh
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
npm ci
cp .env.example .env.local
npm run db:validate
npm run db:deploy
.venv/bin/python -m uvicorn app.main:app --reload --env-file .env.local
```

The API listens on `http://127.0.0.1:8000`; generated docs are at `/docs` and
`/openapi.json`. Use a Supabase direct connection or session pooler on port
5432. The transaction pooler on port 6543 is not supported.

## Landing site

```sh
cd landing
npm ci
npm run dev
```

Next.js uses port 3000 by default.

## Documentation site

From the repository root:

```sh
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r docs/requirements.txt
NO_MKDOCS_2_WARNING=true .venv-docs/bin/mkdocs serve -a 127.0.0.1:8001
```

The site is available at `http://127.0.0.1:8001/linguini/`. A strict build
writes ignored output to `site/`:

```sh
NO_MKDOCS_2_WARNING=true .venv-docs/bin/mkdocs build --strict
```

## Without Supabase: throwaway PostgreSQL

```sh
docker run -d --name linguini-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=linguini_test \
  -p 5432:5432 \
  postgres:16
```

```sh
export DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5432/linguini_test?sslmode=disable'
export DIRECT_URL="$DATABASE_URL"
export TEST_DATABASE_URL="$DATABASE_URL"
```

Run `npm run db:deploy` from `backend/`. Migrations do not create a learner
account. For `AUTH_MODE=demo`, set `DEMO_USER_ID` to an existing `users.id` and
insert a matching row on a fresh database:

```sql
INSERT INTO users (id, auth_provider_id, display_name, email)
VALUES (
  '11111111-1111-4111-8111-111111111111',
  'local-demo-user',
  'Local Demo',
  'local@example.test'
);
```

Set `AUTH_MODE=demo` and
`DEMO_USER_ID=11111111-1111-4111-8111-111111111111`. This bypasses bearer-token
verification for local/test requests only. Upload URLs and signed media still
require `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

## Backend environment

### Core

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Runtime PostgreSQL connection. |
| `DIRECT_URL` | Prisma migration connection. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser origins. |
| `VISION_PROVIDER` | Legacy vision provider setting. |
| `VISION_MODEL_NAME` | Legacy vision model name. |
| `VISION_TIMEOUT_SECONDS` | Legacy vision timeout. |
| `VISION_MAX_OUTPUT_TOKENS` | Legacy vision output cap. |
| `VISION_MAX_RETRIES` | Legacy vision retry count. |

### Auth

| Variable | Purpose |
| --- | --- |
| `AUTH_MODE` | `supabase` or `demo`. |
| `SUPABASE_JWT_AUDIENCE` | JWT audience checked by verification. |
| `SUPABASE_JWT_SECRET` | Optional legacy HS256 secret. |
| `AUTH_ALLOW_ANONYMOUS` | Accept anonymous Supabase identities when true. |
| `DEMO_USER_ID` | Existing user ID used in demo mode. |

### Storage

| Variable | Purpose |
| --- | --- |
| `MEDIA_STORAGE_PRIVATE` | Use private signed media URLs. |
| `SUPABASE_URL` | Supabase project URL. |
| `MEDIA_STORAGE_BUCKET` | Storage bucket, normally `media-assets`. |
| `SUPABASE_SERVICE_ROLE_KEY` | Backend-only Storage credential. |
| `MEDIA_PUBLIC_BASE_URL` | Public media base URL when private URLs are off. |

### AI per feature

The provider/model/timeout/output/retry pattern is repeated for
`SCENE_ANALYSIS`, `SCENE_TRANSLATION`, `LEARNING_TASK`, `ISPY_CLUE`, and
`ISPY_GUESS`:

| Variable pattern | Purpose |
| --- | --- |
| `AI_<FEATURE>_PROVIDER` | `openai`, `gemini`, `openrouter`, or `none`. |
| `AI_<FEATURE>_MODEL` | Provider model identifier. |
| `AI_<FEATURE>_TIMEOUT_SECONDS` | Request timeout. |
| `AI_<FEATURE>_MAX_OUTPUT_TOKENS` | Optional output cap. |
| `AI_<FEATURE>_MAX_RETRIES` | Optional repair/retry count. |

Checked-in defaults are OpenRouter routes: scene analysis
`anthropic/claude-haiku-4.5`, translation `openai/gpt-4o-mini`, learning tasks
`openai/gpt-5.4-mini`, I-Spy clue `google/gemini-3.1-flash-lite`, and I-Spy
guess `openai/gpt-4.1-mini`.

| Variable | Purpose |
| --- | --- |
| `AI_MODE` | `demo` deterministic mode or `real` configured providers. |
| `AI_OPENAI_API_KEY` | OpenAI provider key. |
| `AI_GEMINI_API_KEY` | Gemini provider key. |
| `AI_OPENROUTER_API_KEY` | OpenRouter provider key used by defaults. |
| `AI_API_KEY` | General/custom key; not used by default wiring. |
| `AI_OBJECT_GROUNDING_PROVIDER` | `none` or `groundingDino`. |
| `AI_OBJECT_GROUNDING_MODEL` | Grounding model identifier. |
| `AI_OBJECT_GROUNDING_THRESHOLD` | Grounding score threshold. |
| `AI_OBJECT_GROUNDING_MAX_LABELS` | Maximum queried labels. |
| `AI_OBJECT_GROUNDING_MAX_IMAGE_SIDE` | Detector resize bound. |
| `AI_IMAGE_MODERATION_PROVIDER` | `none` or `openai`. |
| `AI_IMAGE_MODERATION_MODEL` | Moderation model identifier. |
| `AI_IMAGE_MODERATION_TIMEOUT_SECONDS` | Moderation timeout. |

### Observability

| Variable | Purpose |
| --- | --- |
| `AI_OBSERVABILITY_ENABLED` | Enable Langfuse tracing. |
| `AI_OBSERVABILITY_BASE_URL` | Langfuse endpoint. |
| `AI_OBSERVABILITY_PUBLIC_KEY` | Langfuse public key. |
| `AI_OBSERVABILITY_SECRET_KEY` | Langfuse secret key. |
| `AI_OBSERVABILITY_ENVIRONMENT` | Trace environment label. |
| `AI_OBSERVABILITY_CAPTURE_CONTENT` | Opt-in content capture; defaults false. |

### Background workers

`BACKGROUND_WORKERS` controls the production
`ThreadPoolBackgroundRunner` worker count and defaults to `4`. Tests generally
use the synchronous `InlineBackgroundRunner`.

## Frontend environment

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Backend origin used by the browser API client. |
| `VITE_SUPABASE_URL` | Supabase project URL for the browser client. |
| `VITE_SUPABASE_ANON_KEY` | Publishable Supabase browser key. |

## Precomputing curated scenes

`python -m app.scripts.precompute_preloaded_scenes` computes translated
suggestions for bundled scenes. Main flags are:

```text
--slug SLUG             repeatable base scene selection
--language {fr,es}      repeatable target language selection
--dry-run               validate without database writes
--json PATH             write computed rows and assets
--from-json PATH        reuse an artifact without AI calls
--emit-migration PATH   write INSERT ... ON CONFLICT SQL
--env-file PATH         dotenv file (default .env.local)
```

Without flags it processes all bundled scenes for French and Spanish.
