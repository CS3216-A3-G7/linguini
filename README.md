# Linguini

A photo-led, speak-first language-learning app: explore a scene, learn its words,
then play I-Spy with Linguini in both directions.

## Current status

This repository contains a React/TypeScript frontend and a FastAPI/Pydantic backend.
The frontend runs independently with mock data and in-memory state, which resets on
refresh. Scene images are SVG placeholders; word playback uses browser speech synthesis
when available.

The backend defines API routes and validated request/response schemas. Its health
endpoint works; business route handlers return `501 Not Implemented` when reached.
Authentication, persistence, AI services, and frontend API integration are not
implemented yet. No API keys or database configuration are needed for this prototype.

## Repository layout

```text
linguini/
|-- frontend/             React app and frontend tooling
|   |-- src/
|   |   |-- components/   Shared UI, app shells, and scene rendering
|   |   |-- data/         Mock data and frontend types
|   |   |-- lib/          Browser speech helper
|   |   |-- pages/        Screen components
|   |   |-- state/        In-memory learner and session state
|   |   `-- styles/       Global styles and design tokens
|   |-- public/          Static assets
|   |-- package.json     npm scripts and dependencies
|   `-- vite.config.ts   Vite configuration
|-- backend/
|   |-- app/             FastAPI entrypoint, routes, and schemas
|   |-- tests/           API contract and schema tests
|   `-- pyproject.toml   Python dependencies and tooling
|-- .oxlintrc.json       Frontend lint configuration
|-- design.md            Product design and visual guidelines
`-- README.md
```

Each app manages its own dependencies. Run npm commands in `frontend/` and Python
commands in `backend/`. Keep the backend virtual environment in `backend/.venv/`,
which is ignored by Git.

## Run locally

### Frontend

Use Node.js 22.12+ on the Node 22 line, or Node 24, with npm.

From the repository root:

```sh
cd frontend
npm ci
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.
The backend does not need to be running to explore the current UI.

### Backend

Use Python 3.12 or newer. In a separate Windows PowerShell terminal, starting
from the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Skip environment creation if `backend/.venv` already exists.
Open `http://127.0.0.1:8000/docs` for the API documentation.
See the [backend README](backend/README.md) for macOS/Linux setup and API details.

## Frontend commands

Run these inside `frontend/`:

| Command | Purpose |
| --- | --- |
| `npm ci` | Install dependencies from the committed lockfile |
| `npm run dev` | Start the development server |
| `npm run build` | Typecheck and build production assets into `dist/` |
| `npm run lint` | Run Oxlint |
| `npm run preview` | Preview an existing production build locally |

There is currently no frontend test script. Backend test and lint commands are
documented in the [backend README](backend/README.md#checks).

## Screens

These are frontend routes, separate from the backend's `/api/v1` endpoints.

| Route | Screen |
| --- | --- |
| `/` | Welcome |
| `/onboarding` | Account, language, goal, and permission setup UI |
| `/login` | Login UI |
| `/home` | Home and practice entry point |
| `/practice` | Scene selection |
| `/practice/:sceneId/analysis` | Scene analysis and word markers |
| `/practice/:sceneId/mic-test` | Microphone setup UI and typing fallback |
| `/practice/:sceneId/learn` | Learning tasks and flashcards |
| `/practice/:sceneId/ispy-1` | I-Spy: Linguini gives clues |
| `/practice/:sceneId/ispy-2` | I-Spy: the learner gives clues |
| `/practice/:sceneId/summary` | Session summary |
| `/progress` | Progress, scenarios, and leaderboard |
| `/vocabulary` | Vocabulary and status filters |
| `/journal`, `/journal/new`, `/journal/:entryId` | Journal list, creation, and entry |
| `/profile` | Profile and preferences |

## Development notes

Use [design.md](design.md) and `frontend/src/styles/tokens.css` for visual conventions.
Frontend types and backend schemas are currently maintained separately. When
connecting the apps, align the UI with the backend OpenAPI contracts and configure
the API URL plus a development proxy or backend CORS support; neither is configured yet.
