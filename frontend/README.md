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

Open **http://127.0.0.1:9000** in your browser.

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
│   └── pages/
│       ├── dashboard.py     # Home — stats + recent activity
│       ├── test_cases.py    # Placeholder
│       ├── code_review.py   # Placeholder
│       └── settings.py      # Placeholder
├── requirements.txt
└── README.md
```

## Pages

| Route | Page | Status |
|-------|------|--------|
| `/` | Dashboard | Implemented — metric cards and recent activity |
| `/test-cases` | Test case generation | Implemented — fetch ticket, generate, results, export actions |
| `/code-review` | PR code review | Implemented — fetch diff, AI review, comment cards |
| `/settings` | Integration settings | Implemented — JIRA, Git, TestRail, LLM forms |

## API integration

The dashboard calls:

- `GET /api/v1/activity/summary` — metric cards
- `GET /api/v1/activity/recent?limit=20` — activity list

When the backend returns non-200 (e.g. 501 Not Implemented), the UI falls back to demo data matching the mockup so you can develop the UI independently.

## Next steps

1. Test cases page — JIRA ticket input, generation spinner, case editor
2. Code review page — PR URL input, diff viewer, comment triage
3. Settings page — integration forms wired to backend Settings API
4. Replace demo fallback once backend activity endpoints are implemented
