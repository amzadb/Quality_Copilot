# Quality Copilot

A tool for AI-assisted QA workflows: generate test cases from JIRA tickets, export to local files / JIRA / TestRail, and run AI-powered pull request code reviews.

The project is split into a **FastAPI backend** (`backend/`) and a **NiceGUI frontend** (`frontend/`). The frontend calls the backend at `/api/v1` and falls back to demo data when the API is unavailable or not yet implemented.

## Repository layout

```
Quality_Copilot/
├── backend/          # FastAPI REST API (port 8000)
├── frontend/         # NiceGUI web UI (port 9000)
└── README.md         # This file
```

| Component | Stack | Default URL |
|-----------|-------|-------------|
| Backend | FastAPI, Pydantic, SQLAlchemy (stubs) | http://127.0.0.1:8000 |
| Frontend | NiceGUI, httpx | http://127.0.0.1:9000 |

## Prerequisites

- Python 3.10 or later
- pip

Each component uses its own virtual environment under `backend/.venv` and `frontend/.venv`.

## Quick start

Run both services in separate terminals:

```powershell
# Terminal 1 — Backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
cd frontend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

Then open **http://127.0.0.1:9000** in your browser.

Useful backend URLs:

| URL | Purpose |
|-----|---------|
| http://127.0.0.1:8000/health | Health check |
| http://127.0.0.1:8000/docs | Swagger UI |
| http://127.0.0.1:8000/api/v1/... | Versioned API |

## Frontend pages

| Route | Description |
|-------|-------------|
| `/` | Dashboard — activity summary and recent runs |
| `/test-cases` | Fetch JIRA ticket, generate test cases, inline edit, export dialogs |
| `/code-review` | Fetch PR, run AI review, triage comments |
| `/settings` | Configure JIRA, Git provider, TestRail, and LLM integrations |

## Configuration

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_NAME` | `Quality Copilot` | OpenAPI application title |
| `API_V1_PREFIX` | `/api/v1` | API base path |
| `DEBUG` | `false` | Debug mode |
| `DATABASE_URL` | `sqlite:///./quality_copilot.db` | SQLAlchemy database URL |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_TITLE` | `Quality Copilot` | Browser tab title |
| `BACKEND_URL` | `http://127.0.0.1:8000` | Backend base URL |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |
| `PORT` | `9000` | NiceGUI server port |
| `RELOAD` | `true` | Auto-reload on code changes |
| `STORAGE_SECRET` | local-dev default | NiceGUI user session storage (required for login) |

Integration secrets (JIRA, Git, TestRail, LLM) are stored **per user** in the database after login. `credentials.json` remains a legacy shared fallback for unauthenticated/legacy clients. Secrets are never returned in full on GET.

Auth: open **http://127.0.0.1:9000/login** — seed admin defaults to `admin` / `admin` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`). Set `JWT_SECRET` (and `STORAGE_SECRET`) for any shared environment.

Apply database migrations before first use:

```powershell
cd backend
.venv\Scripts\activate
alembic upgrade head
```

## Implementation status

| Layer | Status |
|-------|--------|
| **Frontend** | UI complete — login/register, all pages, dialogs, Bearer API client |
| **Backend** | Phase 0–3 + JWT auth and per-user settings |

The frontend works end-to-end with demo/mock data when the backend is down or stubbed, so UI development can proceed independently (after login when the API is up).

## Architecture

```
NiceGUI frontend (9000)
        │  HTTP /api/v1
        ▼
FastAPI backend (8000)
        │
        ├── api/routes/      Thin routers
        ├── services/        Orchestration (test cases, code review, settings, activity)
        ├── integrations/    JIRA, Git provider, TestRail, LLM clients
        ├── models/          SQLAlchemy persistence (stubs)
        └── jobs/            Background tasks (MVP via BackgroundTasks)
```

## Further reading

- [backend/README.md](backend/README.md) — API overview, error handling, project structure, testing
- [frontend/README.md](frontend/README.md) — UI structure, configuration, API integration details
- [PROGRESS.md](PROGRESS.md) — Multi-agent backend implementation tracker
- [docs/API_CONTRACT.md](docs/API_CONTRACT.md) — REST API contract (v1)
