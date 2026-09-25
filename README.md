# Linguini

<p align="center">
  <img src="frontend/public/linguini-logo.png" alt="Linguini logo" width="180" />
  <img src="frontend/public/linguini-wordmark.png" alt="Linguini wordmark" width="360" />
</p>

<p align="center"><strong>Learn the language of your day</strong></p>

## Group members

| Matriculation number | Name | Contribution to the assignment |
| --- | --- | --- |
| `A0312075N` | `Ananya Jain` | `Idea, Branding, Frontend, UI/UX, AI Core Tech, Pitch` |
| `A0286908L` | `Govindaraj Roshni Daksha` | `Backend API, Database, AI Core Tech` |
| `TBC` | `Madrid Lim` | `Landing Page, Marketing, User Analytics, Database` |
| `TBC` | `Shamit Gupta` | `AI Model Analysis, OpenRouter Integration` |


## Repository

| Directory | What it is | Stack | Docs |
| --- | --- | --- | --- |
| [`frontend/`](frontend) | The learner web app | React 19, TypeScript, Vite | [frontend/README.md](frontend/README.md), [design.md](frontend/design.md) |
| [`backend/`](backend) | API, persistence and AI features | FastAPI, SQLAlchemy, PostgreSQL/Supabase, Prisma migrations | [backend/README.md](backend/README.md) |
| [`landing/`](landing) | Marketing site with an interactive demo session | Next.js 16 (App Router) | [landing/README.md](landing/README.md) |
| [`marketing/`](marketing) | Product Hunt launch kit, launch videos, media kit and business model | Markdown, Python/Pillow, FFmpeg, Hyperframes | [marketing/README.md](marketing/README.md) |

Each app manages its own dependencies and deploys on its own. `marketing/` is not deployed; it holds source files and finished exports.

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

## Significant resources

- [React documentation](https://react.dev/learn) — component-based UI development.
- [Vite documentation](https://vite.dev/guide/) — frontend development and production builds.
- [FastAPI documentation](https://fastapi.tiangolo.com/) — backend API design and interactive API documentation.
- [PostgreSQL documentation](https://www.postgresql.org/docs/) — relational data modelling and database behaviour.
- [Supabase documentation](https://supabase.com/docs) — managed PostgreSQL, authentication, storage, and database services.
- [Google People + AI Guidebook](https://pair.withgoogle.com/guidebook/patterns) — human-centred AI interaction patterns, including user control, system status, and error recovery.
- [Microsoft HAX Toolkit](https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/) — evidence-based guidelines for human–AI interaction and correcting AI output.
- [Impeccable](https://impeccable.style/) — design guidance used during interface refinement to improve hierarchy, spacing, typography, and consistency.
- [OpenAI prompt engineering guidance](https://platform.openai.com/docs/guides/prompt-engineering) — prompt structure, clear instructions, and output constraints.
- [Google Gemini API documentation](https://ai.google.dev/gemini-api/docs) — multimodal model integration and structured AI responses.

## Contributing

- Branch from `main` with a plain descriptive slug, e.g. `session-lifecycle`, and open one pull request per slice of work.
- Commits and pull requests are attributed to the team member who requested the work. AI agents must not add themselves as authors or co-authors, or add "Generated with" lines; the CI `attribution` job rejects pull requests that do.
- Run the checks before opening a pull request:

  ```sh
  cd frontend && npm ci && npm run lint && npm run build
  cd backend  && ruff check . && pytest
  cd landing  && npm ci && npm run lint && npm run build
  ```

- Backend integration tests need `TEST_DATABASE_URL` pointing at a disposable PostgreSQL database.
- Keep credentials in ignored `.env.local` files. Never commit database URLs, Supabase keys or API keys.

More agent-facing conventions live in [AGENTS.md](AGENTS.md).
