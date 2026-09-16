# Linguini backend

FastAPI/Pydantic v2 contract skeleton for the Linguini learning flow.

## What is implemented

- Modular Pydantic schemas for users, language profiles, media, detected scene
  objects, vocabulary, sessions, learning tasks, I-Spy, attempts, journals,
  suggestions, word mentions, and AI observability.
- Versioned `/api/v1` routes with request and response contracts.
- Camel-case API JSON backed by snake-case Python attributes.
- Validation for normalized bounding boxes, session/task terminal states,
  discriminated task and attempt payloads, and once-daily journal data.
- A client-safe task response that cannot include the private answer key.

The domain services and persistence layer are deliberately not faked in this
branch. Except for health, route handlers return `501 Not Implemented` until a
service is connected. This keeps OpenAPI usable without putting business logic
inside route functions.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the generated API documentation.

## Test

```bash
pytest
ruff check .
```

## Layout

```text
app/
├── api/
│   ├── router.py
│   └── routes/
└── schemas/
```

Add business logic next under `app/services/`, and persistence adapters under
`app/repositories/`. Route handlers should authenticate, validate, call one
service method, and return its result.
