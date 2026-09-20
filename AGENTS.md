# Linguini agent guide

Linguini is a photo-led, speak-first language-learning app. The repository is a monorepo:

- `frontend/` — React 19 + TypeScript + Vite SPA. See `frontend/AGENTS.md` for UI conventions (note: its "Current checkout" section describes an older root-level prototype and is out of date).
- `backend/` — FastAPI + Pydantic + SQLAlchemy on PostgreSQL/Supabase, with Prisma owning migrations. API prefix `/api/v1`.

## Branch and pull request conventions

- Name branches with a plain descriptive slug: `session-lifecycle`, `journal-day-photos`, `vocabulary-evidence-xp`. Do not prefix branches with `devin/` or a timestamp.
- Commits and pull requests are attributed to the team member who requested the work, not to an agent account. Agents must open pull requests on that person's behalf rather than under their own identity.
- One branch per slice of work, opened against `main`.

## Checks before opening a pull request

```sh
cd frontend && npm ci && npm run lint && npm run build
cd backend  && ruff check . && pytest
```

Backend tests need `TEST_DATABASE_URL` pointing at a disposable PostgreSQL database; without it the PostgreSQL integration tests skip silently. Prisma migrations are validated with `npm run db:validate` and applied with `npm run db:deploy` from `backend/`.

## Safety

- Keep credentials in ignored local environment files (`.env.local`). Never commit database URLs, Supabase keys, or API keys.
- Migrations run against a live Supabase project; treat any schema change as destructive until reviewed.
