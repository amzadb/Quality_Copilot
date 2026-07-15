# Quality Copilot — Frontend

NiceGUI web UI for **Quality Copilot**. The dashboard matches the design mockup with metric cards, recent activity feed, and sidebar navigation.

## Prerequisites

- Python 3.10 or later
- Backend API running at `http://127.0.0.1:8000` (optional — demo data is used when the API is unavailable)

## Quick start

```powershell
cd frontend

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

pip install -r requirements.txt

python -m app.main
```

Open **http://127.0.0.1:9000/login** in your browser. Sign in with the seeded admin (`admin` / `admin` by default) or create an account.

Run alongside the backend:

```powershell
# Terminal 1 — backend
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
.venv\Scripts\activate
python -m app.main
```

## Configuration

Set via environment variables or a `.env` file in the `frontend/` directory:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_TITLE` | `Quality Copilot` | Browser tab title and sidebar heading |
| `BACKEND_URL` | `http://127.0.0.1:8000` | FastAPI backend base URL |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |
| `PORT` | `9000` | NiceGUI server port |
| `RELOAD` | `true` | Auto-reload on code changes |
| `STORAGE_SECRET` | local-dev default | Secret for NiceGUI `app.storage.user` (login session) |

## Project structure

```
frontend/
├── app/
│   ├── main.py              # Routes and ui.run entry point
│   ├── config.py            # Environment settings
│   ├── api/
│   │   └── client.py        # Backend HTTP client + demo fallback data
│   ├── components/
│   │   ├── layout.py        # Sidebar shell and global styles
│   │   ├── stat_card.py     # Dashboard metric cards
│   │   ├── activity_list.py # Recent activity rows and badges
│   │   └── styles.py        # CSS matching the mockup
│   ├── auth.py              # JWT session helpers (NiceGUI storage)
│   └── pages/
│       ├── login.py         # Login / sign-up
│       ├── dashboard.py     # Home — stats + recent activity
│       ├── test_cases.py
│       ├── code_review.py
│       └── settings.py
├── requirements.txt
└── README.md
```

## Pages

| Route | Page | Status |
|-------|------|--------|
| `/login` | Login / Sign up | JWT via backend; token in `app.storage.user` |
| `/` | Dashboard | Requires auth — metric cards and recent activity |
| `/test-cases` | Test case generation | Requires auth |
| `/code-review` | PR code review | Requires auth |
| `/settings` | Integration settings | Per-user settings after login |

## API integration

The UI talks to the FastAPI backend at `/api/v1` with `Authorization: Bearer <token>`. On `401`, the session is cleared and the user is sent to `/login`.

Demo/mock data is used **only when the backend is unreachable** (connection/timeout). HTTP 4xx/5xx from a live API are surfaced to the UI — they are not silently replaced with demo success. Empty `/activity/recent` lists are kept as empty (not replaced by a fake feed).

Contract reference: [`docs/API_CONTRACT.md`](../docs/API_CONTRACT.md).
