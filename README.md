# Linguini

Linguini is a photo-led, speak-first language-learning app. You photograph a moment from your day, Linguini finds the words inside it, you practise them through word cards, I-Spy and short sentence tasks in Spanish or French, and the day ends up in your journal.

## Repository

| Directory | What it is | Stack | Docs |
| --- | --- | --- | --- |
| [`frontend/`](frontend) | The learner web app | React 19, TypeScript, Vite | [frontend/README.md](frontend/README.md), [design.md](frontend/design.md) |
| [`backend/`](backend) | API, persistence and AI features | FastAPI, SQLAlchemy, PostgreSQL/Supabase, Prisma migrations | [backend/README.md](backend/README.md) |
| [`landing/`](landing) | Marketing site with an interactive demo session | Next.js 16 (App Router) | [landing/README.md](landing/README.md) |

Each app manages its own dependencies and deploys on its own.

## Quick start

```sh
# Learner app (http://localhost:5173)
cd frontend && npm ci && cp .env.example .env.local && npm run dev

# API (http://127.0.0.1:8000/docs); fill DATABASE_URL and DIRECT_URL in .env.local first
cd backend && python -m venv .venv && .venv/bin/pip install -e ".[dev]" && npm ci \
  && cp .env.example .env.local && npm run db:deploy \
  && .venv/bin/uvicorn app.main:app --reload --env-file .env.local

# Landing page (http://localhost:3000)
cd landing && npm ci && npm run dev
```

Windows/PowerShell setup, environment variables and API details are in the app READMEs.

## Contributing

- Branch from `main` with a plain descriptive slug, e.g. `session-lifecycle`, and open one pull request per slice of work.
- Commits and pull requests are attributed to the team member who requested the work.
- Run the checks before opening a pull request:

  ```sh
  cd frontend && npm ci && npm run lint && npm run build
  cd backend  && ruff check . && pytest
  cd landing  && npm ci && npm run lint && npm run build
  ```

- Backend integration tests need `TEST_DATABASE_URL` pointing at a disposable PostgreSQL database.
- Keep credentials in ignored `.env.local` files. Never commit database URLs, Supabase keys or API keys.

More agent-facing conventions live in [AGENTS.md](AGENTS.md).
