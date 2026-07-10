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

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_TITLE` | `Quality Copilot` | Browser tab title |
| `BACKEND_URL` | `http://127.0.0.1:8000` | Backend base URL |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |
| `PORT` | `9000` | NiceGUI server port |
| `RELOAD` | `false` | Auto-reload on code changes |

Integration secrets (JIRA, Git, TestRail, LLM) are stored server-side via the Settings API and are never returned in full on GET requests.

## Implementation status

| Layer | Status |
|-------|--------|
| **Frontend** | UI complete — all pages, dialogs, inline editing, and comment triage wired to the API client |
| **Backend** | Skeleton — all endpoints registered in OpenAPI; business logic returns **501 Not Implemented** until integrations are built |

The frontend works end-to-end with demo/mock data when the backend is down or stubbed, so UI development can proceed independently.

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
