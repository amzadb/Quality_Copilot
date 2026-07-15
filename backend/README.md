# Quality Copilot — Backend

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
| `CREDENTIALS_PATH` | `./data/credentials.json` | Server-side integration secrets (never returned on GET) |
| `JIRA_EMAIL` | _(none)_ | Atlassian account email for JIRA API token auth |
| `ANTHROPIC_MODEL` | `claude-sonnet-5` | Claude model for LLM integration |
| `ANTHROPIC_API_VERSION` | `2023-06-01` | Anthropic API version header |

Copy `.env.example` to `.env` and adjust as needed. Integration secrets (JIRA, Bitbucket/GitHub/GitLab, TestRail, LLM) will be stored server-side via the Settings API once implemented — they are never returned in full by GET requests.

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
├── app/
│   ├── main.py                    # FastAPI app factory, exception handlers, /health
│   ├── config.py                  # Environment-backed settings
│   ├── api/routes/                # Thin FastAPI routers (one module per domain)
│   ├── schemas/                   # API request/response Pydantic models
│   ├── services/                  # Orchestration layer
│   │   ├── test_case_service.py   # JIRA → LLM → export → TestRail
│   │   └── code_review_service.py # Git → LLM → review runs
│   ├── integrations/              # External system clients
│   │   ├── jira.py
│   │   ├── git_provider.py
│   │   ├── llm.py                 # Prompt templates + structured output models
│   │   └── testrail.py
│   ├── models/                    # SQLAlchemy DB models (tickets, runs, jobs, …)
│   │   └── base.py                # Declarative base, engine, SessionLocal, get_db()
│   ├── jobs/                      # Background task runner (BackgroundTasks MVP)
│   └── core/
│       └── errors.py              # AppError + consistent error response shape
├── alembic/                       # Database migrations
├── alembic.ini
├── tests/                         # pytest suite (mirrors app/ concerns)
├── requirements.txt
└── README.md
```

### Architecture

Thin **routes** validate input and delegate to **services** (or directly to **integrations** for simple reads). Services orchestrate integrations, persist via **models**, and enqueue work through **jobs**.

```
HTTP request → api/routes → service (orchestration)
                              ├── integrations/ (JIRA, Git, LLM, TestRail)
                              ├── models/       (persistence)
                              └── jobs/         (async export, upload, post-back)
                    ↓
              schemas/ (API contract validation)
```

## API overview

All endpoints are prefixed with `/api/v1`.

| Group | Endpoints | Description |
|-------|-----------|-------------|
| **Settings** | `GET/PUT /settings`, `POST /settings/{integration}/test` | Integration config (secrets masked on read) |
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
| **Integrations + Settings** | JIRA, Bitbucket, TestRail, Claude LLM clients; settings persistence |
| **Orchestration services** | Live — test case generation/export/push-back, AI code review, activity dashboard |

Apply migrations after pull: `alembic upgrade head` (includes `002_orchestration`).

## Error handling

All API errors follow a consistent shape:

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

Use `not_implemented_yet()` in skeleton services until real logic is added.

## Testing endpoints locally

### Swagger UI

1. Start the server with `uvicorn app.main:app --reload`
2. Open http://127.0.0.1:8000/docs
3. Expand an endpoint, click **Try it out**, and execute

### curl

```powershell
# Health check
curl http://127.0.0.1:8000/health

# Settings (returns 501 until implemented)
curl http://127.0.0.1:8000/api/v1/settings

# Generate test cases
curl -X POST http://127.0.0.1:8000/api/v1/test-cases/generate `
  -H "Content-Type: application/json" `
  -d "{\"ticket_key\": \"PROJ-1042\"}"
```

### Python TestClient

`httpx` is included in `requirements.txt` for FastAPI's test client and future outbound API calls. **`httpx2`** (Pydantic-stewarded successor to `httpx`) is an optional later migration if Starlette's TestClient deprecation warning becomes blocking — not required for Phase 0/1.

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.get("/api/v1/settings")
assert response.status_code == 501
assert response.json()["error"]["code"] == "NOT_IMPLEMENTED"
```

## Production notes

For production deployment, run uvicorn without `--reload` and consider:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Long-running LLM endpoints (`POST /test-cases/generate`, `POST /reviews/generate`) are synchronous in v1 — expect 10–60 second response times. Configure frontend timeouts accordingly.

## Next steps

1. Settings persistence (encrypted credential storage)
2. Wire integrations (JIRA, TestRail, Git provider, LLM)
3. Database setup (SQLAlchemy engine, Alembic migrations)
4. Implement orchestration in `test_case_service` and `code_review_service`
5. Background tasks in `jobs/tasks.py` for export and upload flows
