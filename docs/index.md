# Linguini

Linguini is a photo-led, speak-first language-learning app. A learner starts
with a ready-made scene or a photo, learns useful words from what they can see,
and then uses those words in guided practice.

## The learner loop

1. **Choose or upload a scene.** Select a curated scene or provide an image.
2. **Learn its vocabulary.** Linguini identifies useful objects and introduces
   their vocabulary in the selected language.
3. **Play two-direction I-Spy.** The learner first identifies Linguini's clue,
   then describes an object back to Linguini.
4. **Write a journal entry.** The learner uses the new words in a once-daily
   journal entry.

The current frontend exposes the learning flow through routes such as
`/practice`, `/practice/sessions/:sessionId/learn`, the two I-Spy phases, and
`/journal`.

## Technology stack

- **Frontend:** React 19, Vite 8, and TypeScript.
- **Backend:** FastAPI, Pydantic, SQLAlchemy, and psycopg.
- **Database:** PostgreSQL, normally hosted by Supabase.
- **Migrations:** Prisma owns the schema and migrations; the Python runtime
  uses SQLAlchemy for application queries.

The frontend talks to the backend's `/api/v1` HTTP API. It does not connect to
PostgreSQL directly.

## Current status

This is an honest description of the current implementation, not a roadmap:

- There is no authentication. The backend currently uses a configured demo
  user ID and that identity is not authentication.
- AI generation, speech evaluation, and real image analysis are not
  implemented. Uploaded-image analysis uses placeholder workflow data.
- Some business routes intentionally return `501 Not Implemented`.
- PostgreSQL persistence covers the implemented user, profile, scene, practice,
  vocabulary, progress, journal, and observability paths.
- Supabase Storage is used for media bytes when storage-backed features are
  configured; database migrations and most local tests do not require Supabase
  credentials.

## Where to go next

- [Architecture](architecture.md) — repository boundaries, API modules, and
  frontend routes.
- [Local development](local-development.md) — install, configure, migrate, and
  run the apps, including a throwaway local PostgreSQL setup.
- [Testing](testing.md) — local checks, database-test isolation, and CI jobs.
- [Database](database.md) — Prisma models, migration conventions, and a partial
  relationship diagram.
