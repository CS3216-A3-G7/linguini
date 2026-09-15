# Linguini

A photo-led, speak-first language-learning app: capture a scene, learn the words in it, then play
I-Spy with Linguini in both directions.

This repository currently contains the **frontend only**, with dummy data in `src/data/mock.ts`.
No backend, auth, or LLM calls are wired up yet.

## Run it

```bash
npm install
npm run dev
```

Other scripts: `npm run build` (typecheck + production build), `npm run lint`, `npm run preview`.

## Screens

| Route | Screen |
|---|---|
| `/` | Welcome |
| `/onboarding` | First-user onboarding (account, language, goal, permissions) |
| `/login` | Log in, with resume of an interrupted session |
| `/home` | Home — start or resume a practice session |
| `/practice` | Practice step 1 — take / upload / select a scene |
| `/practice/:sceneId/analysis` | Step 2 — analysis result, markers, initial XP |
| `/practice/:sceneId/mic-test` | Step 3 — microphone check with a typing fallback |
| `/practice/:sceneId/learn` | Phase 1 — ordered learning tasks and flashcards |
| `/practice/:sceneId/ispy-1` | I-Spy phase 1 — Linguini gives clues |
| `/practice/:sceneId/ispy-2` | I-Spy phase 2 — the learner gives clues |
| `/practice/:sceneId/summary` | Session summary and next actions |
| `/progress` | Progress, scenarios and leaderboard |
| `/vocabulary` | My vocabulary with status tabs and filters |
| `/journal`, `/journal/new`, `/journal/:entryId` | Journal list, new entry, single entry |
| `/profile` | Profile and preferences |

## Structure

- `src/styles/tokens.css` — design tokens from [`design.md`](./design.md)
- `src/components/` — UI primitives, bottom-nav shell, scene illustrations and markers
- `src/data/` — types plus the dummy scenes, vocabulary, journal and progress data
- `src/state/` — in-memory app state (XP, task completion, vocabulary status, journal entries)
- `src/pages/` — one file per screen

Scene photos are placeholder SVG illustrations (`src/components/SceneArt.tsx`); swap them for real
images when the capture flow is connected.
