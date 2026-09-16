# Linguini backend

FastAPI/Pydantic v2 API contract skeleton for Linguini. See the
[repository README](../README.md) for the frontend and overall project layout.

## Current status

- Versioned `/api/v1` routes cover health, users, home, media, sessions, tasks,
  vocabulary, and journals.
- Pydantic schemas describe language profiles, scene objects, learning tasks,
  I-Spy attempts, journal revisions and suggestions, and AI observability data.
- API JSON uses camelCase; Python attributes use snake_case.
- Validators cover normalized bounding boxes, task content, attempt input modes,
  and completion-state requirements. Public task responses exclude private answers.

`GET /api/v1/health` returns `{"status":"ok"}`. Business route handlers raise
`501 Not Implemented` with error code `service_not_implemented` when reached;
invalid requests can still receive FastAPI validation errors first.

Authentication, domain services, database persistence, media processing, and AI
integrations are not implemented. The schemas model a daily journal, but enforcing
one journal per user/day will require service and persistence logic.
No environment variables, API keys, or database are required for this skeleton.

## Setup

Python 3.12 or newer is required. Start from the repository root.
If `backend/.venv` already exists, skip the environment creation command.

### Windows PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

These commands use the virtual environment directly, so activation is optional.
To activate it, run `.\.venv\Scripts\Activate.ps1`; then `python` refers to that
environment for the rest of the terminal session.

### macOS / Linux

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload
```

The editable install uses `backend/pyproject.toml` and includes the `dev` extra
(HTTPX, pytest, and Ruff). Hatch explicitly packages the `app/` directory.
Run these commands inside `backend/`, where the project configuration lives.

## Local API

| URL | Purpose |
| --- | --- |
| `http://127.0.0.1:8000/api/v1/health` | Health check |
| `http://127.0.0.1:8000/docs` | Interactive Swagger UI |
| `http://127.0.0.1:8000/redoc` | ReDoc API reference |
| `http://127.0.0.1:8000/openapi.json` | Generated OpenAPI schema |

Running this server does not connect the frontend automatically. The frontend
still uses mock data, and no CORS middleware or frontend development proxy is
configured yet.

## Checks

From `backend/` on Windows, without activating the environment:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

With the virtual environment activated on any platform:

```sh
python -m pytest
python -m ruff check .
```

Tests cover the health response, core OpenAPI paths, explicit unimplemented-service
errors, camelCase serialization, bounding boxes, task content, private-answer
exclusion, and discriminated attempt inputs. They do not test end-to-end learning
flows or database behavior.

## Layout

```text
backend/
|-- app/
|   |-- main.py           FastAPI app factory and application instance
|   |-- api/
|   |   |-- router.py     Versioned router assembly
|   |   |-- errors.py     Shared unimplemented-service error
|   |   `-- routes/       Route contracts grouped by feature
|   `-- schemas/          Pydantic models and validation
|-- tests/
|   |-- test_openapi.py   Health and API contract checks
|   `-- test_schemas.py   Model validation and serialization checks
|-- .gitignore           Virtual environment and Python cache exclusions
|-- pyproject.toml       Build, dependencies, pytest, and Ruff configuration
`-- README.md
```

As features are implemented, add domain logic under `app/services/` and persistence
adapters under `app/repositories/`. Keep route handlers focused on HTTP concerns,
authentication, request validation, and calling services. These directories are
planned extension points and do not exist yet.
