# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python FastAPI backend implementing the [RealWorld](https://github.com/gothinkster/realworld) API spec — a Medium.com clone with standardized endpoints across language implementations. Only user registration is currently implemented; the spec requires many more endpoints (articles, comments, profiles, favorites, feed).

## Commands

Dependencies are managed with [uv](https://docs.astral.sh/uv/) (`[project]` table in `pyproject.toml`, pinned in `uv.lock`). Run `uv sync` to create/update the `.venv`; prefix commands with `uv run`.

```bash
# Production-style server (starts Docker DB, waits for it, runs `fastapi run` — no reload, binds 0.0.0.0:8090)
make start

# Dev server with hot reload (starts Docker DB, waits for it, runs `fastapi dev` on 127.0.0.1:8090)
make dev

# Run integration tests (starts test DB, runs hurl against ../realworld/specs/api/run-api-tests-hurl.sh)
make int-tests

# Lint (note: Makefile `lint` target is broken — references golangci-lint; run these directly)
uv run ruff check app/
uv run mypy app/

# Create a migration from model changes (autogenerate)
uv run alembic revision --autogenerate -m "describe change"

# Apply migrations to the dev DB (connection from alembic.ini)
uv run alembic upgrade head
```

Both `make start` and `make dev` serve at `http://localhost:8090`. The Makefile `lint` target is still broken (references a Go linter); use `ruff` and `mypy` directly as shown above.

## Architecture

Layered FastAPI app, organized by responsibility:

- **`app/main.py`** — FastAPI app creation, router inclusion, and exception handlers
- **`app/api/`** — API routers / endpoints (e.g. `users.py`, mounted at `/api/users`)
- **`app/services/`** — business logic (e.g. `UserService` in `user.py`); `custom_errors.py` holds custom exceptions
- **`app/models/`** — SQLAlchemy ORM models (e.g. `User`), mapped on the shared `Base`
- **`app/schemas/`** — Pydantic request/response models (validation + serialization)
- **`app/db/`** — async SQLAlchemy engine, session factory, and the `get_db` dependency (`database.py`)
- **`app/core/`** — `config.py` (pydantic-settings `Settings`)

### Key patterns

- **Pydantic `BaseModel`** for both request validation and response serialization (`app/schemas/`); response models use `ConfigDict(from_attributes=True)` to build from ORM objects
- **SQLAlchemy 2.0 async ORM** — typed `Mapped[...]` / `mapped_column(...)` models; all models share the single `Base` from `app/db/database.py`
- **Dependency injection** via FastAPI `Depends` — `get_db` yields an `AsyncSession`; `UserService` takes that session in its constructor
- **Custom exceptions** (e.g. `DuplicateException` in `app/services/custom_errors.py`) caught in `app/main.py` and mapped to HTTP responses
- **Password hashing** with `pwdlib` (`PasswordHash.recommended()`, argon2)
- **JWT** (PyJWT, HS256) for auth tokens; secret from `Settings.jwt_secret`

### Database

PostgreSQL, accessed via SQLAlchemy's **async engine** (`app/db/database.py`) over the `asyncpg` driver (connection string must use the `postgresql+asyncpg://` scheme). Schema migrations are managed by **Alembic** (async template):

- Migration scripts live in `alembic/versions/`; config in `alembic.ini`; `alembic/env.py` imports the models so autogenerate sees them on `Base.metadata` (import new models there when you add them).
- Create a revision with `alembic revision --autogenerate`, apply with `alembic upgrade head` (see Commands).
- The raw SQL in `migrations/` is **legacy** (from the removed `yoyo` setup) and is kept for reference only — it is not applied by anything.
- Dev DB: `localhost:8095` (Docker via `compose.yaml`)
- Test DB: `localhost:8096` (Docker via `compose.test.yaml`)

### Environment

Config is loaded by **pydantic-settings** (`app/core/config.py`, `Settings`) from `.env` (dev) or `.env_test` (tests). The app only reads `DB_CONNECTION_STRING` (full `postgresql+asyncpg://...` URL) and `JWT_SECRET`; other keys in `.env` (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `SERVER_PORT`) are legacy/unused by the app (`Settings` has `extra="ignore"`).

## Integration Tests

Tests use **Hurl** (HTTP request language) against the RealWorld API spec, located in `../realworld/specs/api/hurl/`. `make int-tests` starts the test DB (`compose.test.yaml`), launches the app via `fastapi`/`uvicorn` on port 8097 with `.env_test` (loaded through `uv run --env-file`), runs the hurl suite, then truncates the `users` table and tears the DB down. It requires the sibling `../realworld` repo to be checked out for the hurl spec. Note: `make int-tests` does **not** create the schema before running, so the test DB needs its tables first. `alembic/env.py` currently reads `sqlalchemy.url` from `alembic.ini` (hardcoded to the dev DB on 8095), so applying migrations to the test DB (8096) means temporarily pointing `sqlalchemy.url` at it before `uv run alembic upgrade head`. Wiring the test-DB migration step into the `int-tests` target (and/or making `env.py` read the URL from the environment) is still a TODO.
