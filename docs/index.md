# Linguini

Linguini is a photo-led, speak-first language-learning app. A learner starts
from a ready-made scene or a personal photo, confirms the useful objects in
that scene, learns their vocabulary, practises both directions of I-Spy, and
records the result in a journal.

The live application is available at
[linguini-navy.vercel.app](https://linguini-navy.vercel.app/).

## The learner loop

1. **Choose or upload a photo.**
2. **Review detected objects.** The analysis screen allows objects, attributes,
   relations, marker positions, and the scene title to be confirmed or edited.
3. **Learn vocabulary.** The backend persists translated scene vocabulary and
   generates learning tasks.
4. **Play two-direction I-Spy.** The learner solves generated clues, then
   describes an object for evaluation.
5. **Write a journal entry.** Journal entries can reference learned words and
   completed-session photos.

## Applications

| Directory | Implementation | Role |
| --- | --- | --- |
| `frontend/` | React 19, Vite, TypeScript | Authenticated learner SPA and session workflow. |
| `backend/` | FastAPI, Pydantic, SQLAlchemy/psycopg | `/api/v1` API, workflow services, AI seams, and PostgreSQL access. |
| `landing/` | Next.js 16 App Router | Independent marketing and interactive-demo site. |
| `marketing/` | Launch kit and media assets | Product Hunt, video, media-kit, and business-model source files; not deployed. |

## What works today

- Supabase bearer-token authentication is implemented. `AUTH_MODE=supabase`
  verifies access tokens against the project JWKS; `AUTH_MODE=demo` provides the
  explicit local/test identity path.
- Curated scenes and uploaded-photo sessions share the persisted session
  workflow. Uploaded scenes can use scene analysis, translation, lesson
  generation, I-Spy clue generation, optional object grounding, and optional
  image moderation.
- Progress is calculated from the idempotent `xp_events` ledger and persisted
  vocabulary encounters. Private media is served through backend-signed URLs.
- The frontend includes account, practice, progress, vocabulary, journal, and
  profile routes. Browser speech is available only as playback through
  `speechSynthesis`.

## Known gaps

- `GET /api/v1/home`, `POST /api/v1/tasks/{task_id}/hints`,
  `POST /api/v1/journals/{journal_id}/suggestions`,
  `GET /api/v1/me/vocabulary/daily`, and
  `GET /api/v1/me/vocabulary/{vocabulary_item_id}` still call the explicit
  `service_not_implemented` helper and return HTTP 501.
- `frontend/src/lib/speech.ts` defines `speak(text, lang)` only. It plays a
  browser voice when available; it does not record audio or grade speech.
- AI features are real code paths, but they are configurable. `AI_MODE=demo`
  or an unconfigured feature selects the deterministic workflow fallback;
  `AI_MODE=real` requires complete provider/model/key configuration.
- Storage-backed upload and signed-image paths still require Supabase Storage
  configuration even though PostgreSQL migrations and most unit tests can run
  locally.

## Where to go next

- [Architecture](architecture.md) — request flow and session lifecycle.
- [API reference](api.md) — routers, response models, errors, and uploads.
- [AI](ai.md) — providers, feature configuration, validation, and tracing.
- [Frontend](frontend.md) — route tree, auth, state, and shared UI.
- [Local development](local-development.md) — all applications and env vars.
- [Testing](testing.md) — local commands, database isolation, and CI.
- [Database](database.md) — current models, constraints, and progress storage.
- [ERD](erd.md) — current PostgreSQL relationships and composite keys.
