# Quality Copilot â€” Backend

FastAPI backend for **Quality Copilot**, an internal tool for AI-assisted test case generation, TestRail/JIRA integration, and pull-request code review. This service exposes a REST API at `/api/v1` for the NiceGUI frontend.

## Prerequisites

- Python 3.10 or later
- pip

## Quick start

```powershell
cd backend

# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Create .env and set JWT_SECRET + CREDENTIALS_ENCRYPTION_KEY (required when DEBUG=false)
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Paste into .env as JWT_SECRET=...
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Paste into .env as CREDENTIALS_ENCRYPTION_KEY=...

# Optional: set ADMIN_PASSWORD in .env to seed an admin on startup (no default password)

# Run the development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The API is available at:

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/health | Health check |
| http://127.0.0.1:8000/docs | Swagger UI (interactive API docs) |
| http://127.0.0.1:8000/redoc | ReDoc API reference |
| http://127.0.0.1:8000/api/v1/... | Versioned API endpoints |

## Configuration

Optional settings can be provided via environment variables or a `.env` file in the `backend/` directory:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Quality Copilot` | Application title shown in OpenAPI docs |
| `API_V1_PREFIX` | `/api/v1` | Base path for all v1 routes |
| `DEBUG` | `false` | Enable debug mode |
| `DATABASE_URL` | `sqlite:///./quality_copilot.db` | SQLAlchemy database URL (SQLite or PostgreSQL) |
| `CREDENTIALS_PATH` | `./data/credentials.json` | Legacy shared secrets file (fallback when unauthenticated) |
| `JWT_SECRET` | _(required)_ | Signs JWTs — **must** be a unique strong value; app refuses to start without it when `DEBUG=false` |
| `CREDENTIALS_ENCRYPTION_KEY` | _(required)_ | Fernet key for encrypting integration tokens at rest |
| `JWT_EXPIRE_MINUTES` | `1440` | Access token lifetime |
| `ADMIN_USERNAME` | `admin` | Username used if admin seed runs |
| `ADMIN_PASSWORD` | _(empty)_ | If set, seeds that admin on startup; **no default password** |
| `JIRA_EMAIL` | _(none)_ | Atlassian account email for JIRA API token auth |
| `ANTHROPIC_MODEL` | `claude-sonnet-5` | Claude model for LLM integration |
| `ANTHROPIC_API_VERSION` | `2023-06-01` | Anthropic API version header |

Copy `.env.example` to `.env` and adjust as needed. Authenticated users store integration secrets in `user_settings` (per user). `credentials.json` is only used as a legacy fallback without a Bearer token. Secrets are never returned in full by GET requests.

## Database setup

Phase 0 adds SQLAlchemy engine/session handling and Alembic migrations.

```powershell
cd backend
.venv\Scripts\activate
pip install -r requirements.txt

# Apply the baseline migration (creates all tables)
alembic upgrade head
```

Useful Alembic commands:

| Command | Purpose |
|---------|---------|
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back one migration |
| `alembic current` | Show current revision |
| `alembic history` | List migration history |

Run tests (from `backend/` with the project venv activated):

```powershell
cd backend
.venv\Scripts\activate
python -m pytest
```

Integration tests call async code via `asyncio.run()` so they do not require the `pytest-asyncio` plugin.

## Project structure

```
backend/
â”œâ”€â”€ app/
â”‚   â”œâ”€â”€ main.py                    # FastAPI app factory, exception handlers, /health
â”‚   â”œâ”€â”€ config.py                  # Environment-backed settings
â”‚   â”œâ”€â”€ api/routes/                # Thin FastAPI routers (one module per domain)
â”‚   â”œâ”€â”€ schemas/                   # API request/response Pydantic models
â”‚   â”œâ”€â”€ services/                  # Orchestration layer
â”‚   â”‚   â”œâ”€â”€ test_case_service.py   # JIRA â†’ LLM â†’ export â†’ TestRail
â”‚   â”‚   â””â”€â”€ code_review_service.py # Git â†’ LLM â†’ review runs
â”‚   â”œâ”€â”€ integrations/              # External system clients
â”‚   â”‚   â”œâ”€â”€ jira.py
â”‚   â”‚   â”œâ”€â”€ git_provider.py
â”‚   â”‚   â”œâ”€â”€ llm.py                 # Prompt templates + structured output models
â”‚   â”‚   â””â”€â”€ testrail.py
â”‚   â”œâ”€â”€ models/                    # SQLAlchemy DB models (tickets, runs, jobs, â€¦)
â”‚   â”‚   â””â”€â”€ base.py                # Declarative base, engine, SessionLocal, get_db()
â”‚   â”œâ”€â”€ jobs/                      # Background task runner (BackgroundTasks MVP)
â”‚   â””â”€â”€ core/
â”‚       â””â”€â”€ errors.py              # AppError + consistent error response shape
â”œâ”€â”€ alembic/                       # Database migrations
â”œâ”€â”€ alembic.ini
â”œâ”€â”€ tests/                         # pytest suite (mirrors app/ concerns)
â”œâ”€â”€ requirements.txt
â””â”€â”€ README.md
```

### Architecture

Thin **routes** validate input and delegate to **services** (or directly to **integrations** for simple reads). Services orchestrate integrations, persist via **models**, and enqueue work through **jobs**.

```
HTTP request â†’ api/routes â†’ service (orchestration)
                              â”œâ”€â”€ integrations/ (JIRA, Git, LLM, TestRail)
                              â”œâ”€â”€ models/       (persistence)
                              â””â”€â”€ jobs/         (async export, upload, post-back)
                    â†“
              schemas/ (API contract validation)
```

## API overview

All endpoints are prefixed with `/api/v1`.

| Group | Endpoints | Description |
|-------|-----------|-------------|
| **Auth** | `POST /auth/register`, `POST /auth/login`, `POST /auth/reset-password`, `GET /auth/me`, `POST /auth/logout` | JWT register/login/reset (public); me/logout require Bearer |
| **Settings** | `GET/PUT /settings`, `POST /settings/{integration}/test` | Per-user integration config (auth required; secrets masked on read) |
| **JIRA** | `GET /jira/tickets/{key}`, `POST .../attachments` | Ticket fetch and file attachment |
| **Test cases** | `POST /test-cases/generate`, run CRUD, save, download, TestRail upload | Generation, export, and push-back |
| **TestRail** | `GET /testrail/projects`, `GET .../suites` | Project/suite dropdowns for upload dialog |
| **Pull requests** | `GET /pull-requests` | PR metadata and diff for code review |
| **Reviews** | `POST /reviews/generate`, run fetch, comment triage | AI code review |
| **Dashboard** | `GET /activity/recent`, `GET /activity/summary` | Recent activity feed and metric cards |

See `/docs` for full request/response schemas.

## Current implementation status

| Layer | Status |
|-------|--------|
| **Foundation** | DB engine/session, Alembic migrations, pytest scaffold |
| **Integrations + Settings** | JIRA, Bitbucket, TestRail, Claude LLM; per-user DB settings + file fallback |
| **Auth** | JWT Bearer, admin seed, self-registration; protected API routers |
| **Orchestration services** | Live — test case generation/export/push-back, AI code review, activity dashboard |
| **QA / contract** | OpenAPI coverage tests; contract error shape for 4xx/422 |

Apply migrations after pull: `alembic upgrade head` (includes `003_users`).

## Error handling

All API errors follow a consistent shape (including validation `422`):

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

Raise `AppError` from services for domain errors:

```python
from app.core.errors import AppError

raise AppError(
    status_code=404,
    code="JIRA_NOT_FOUND",
    message=f"Ticket {ticket_key} was not found.",
)
```

## Testing

```powershell
cd backend
.venv\Scripts\activate
pytest
```

Contract coverage lives in `tests/api/test_contract.py` (OpenAPI path check + mocked end-to-end flow). See also [`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md).

### Swagger UI

1. Start the server with `uvicorn app.main:app --reload --port 8000`
2. Open http://127.0.0.1:8000/docs
3. Expand an endpoint, click **Try it out**, and execute

Long-running LLM endpoints (`POST /test-cases/generate`, `POST /reviews/generate`) are synchronous in v1 — expect 10–60 second response times.
