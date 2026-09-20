# Testing

Run checks from each application directory.

## Frontend checks

```sh
cd frontend
npm ci
npm run lint
npm run build
npm run test
```

The frontend test script uses Node's test runner with TypeScript stripping.
`npm run build` also performs the TypeScript project build.

## Backend checks

Install the development extra in a Python 3.12+ environment, then run:

```sh
cd backend
python3 -m pip install -e ".[dev]"
ruff check .
pytest -q
```

Without `TEST_DATABASE_URL`, approximately 97 PostgreSQL integration tests
skip. For the full suite, point both `TEST_DATABASE_URL` and `DATABASE_URL` at
a disposable database with all Prisma migrations applied:

```sh
TEST_DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5432/linguini_test?sslmode=disable' \
DATABASE_URL='postgresql://postgres:postgres@127.0.0.1:5432/linguini_test?sslmode=disable' \
pytest -q
```

Never point `TEST_DATABASE_URL` at a live Supabase project. The integration
tests write and delete data and require an isolated disposable database.

## CI checks

`.github/workflows/ci.yml` runs four jobs:

- **frontend** installs Node 24 dependencies, then runs lint, build, and tests.
- **database** starts PostgreSQL 16, validates the Prisma schema, deploys all
  migrations, and checks migration status.
- **backend** starts a separate PostgreSQL 16 service, deploys migrations,
  installs the Python development package, and runs Ruff plus the full
  database-backed test suite.
- **docs** installs the pinned MkDocs dependencies and runs
  `mkdocs build --strict`.

The frontend, database, and backend jobs use separate service containers so
their test databases cannot interfere with one another.
