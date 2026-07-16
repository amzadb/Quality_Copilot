# Deploy Quality Copilot on Render

This repo includes a [Render Blueprint](https://render.com/docs/blueprint-spec) at [`render.yaml`](../render.yaml):

| Resource | Name | Role |
|----------|------|------|
| PostgreSQL | `quality-copilot-db` | Auth + per-user settings + run history |
| Web service | `quality-copilot-api` | FastAPI (`/health`, `/api/v1`, `/docs`) |
| Web service | `quality-copilot-web` | NiceGUI UI |

Vercel is not used — NiceGUI needs a long-running server (see root README).

## 1. Deploy from GitHub

1. Push this repo to [amzadb/Quality_Copilot](https://github.com/amzadb/Quality_Copilot) (or your fork).
2. Open [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**.
3. Connect the GitHub repo and apply `render.yaml`.
4. Wait until **quality-copilot-api** and **quality-copilot-db** are live.

## 2. Wire the frontend to the API

The Blueprint sets `BACKEND_HOST` from the API service. The web app builds
`https://<BACKEND_HOST>` automatically.

If Sign up shows **Backend unreachable** / no hits in API logs, the web service is
still pointing at localhost. Fix in the Render dashboard:

1. Open **quality-copilot-api** → copy its URL (e.g. `https://quality-copilot-api.onrender.com`).
2. Open **quality-copilot-web** → **Environment** → set:
   - `BACKEND_URL` = that full URL (**https**, no trailing slash)
3. **Manual Deploy** → restart the web service.
4. In web logs you should see: `Backend API base: https://…/api/v1`

Optional: set `ADMIN_PASSWORD` on the API service to seed an admin on startup. Otherwise use **Sign up** on `/login`.

## 3. Open the app

Use the **quality-copilot-web** URL, e.g. `https://quality-copilot-web.onrender.com/login`.

## Free-tier notes

- Services **sleep after ~15 minutes** idle; the first request can take 30–60+ seconds.
- SQLite is not used on Render — the Blueprint attaches Postgres via `DATABASE_URL`.
- Local files under `/tmp` (legacy `credentials.json`) are ephemeral; prefer Settings after login (DB-backed).
- Keep `JWT_SECRET`, `CREDENTIALS_ENCRYPTION_KEY`, and `STORAGE_SECRET` as Render-generated values (do not commit them).

## Manual env checklist

**API**

| Variable | Required | Notes |
|----------|----------|--------|
| `DATABASE_URL` | yes | From Render Postgres (Blueprint sets this) |
| `JWT_SECRET` | yes | Blueprint can generate |
| `CREDENTIALS_ENCRYPTION_KEY` | yes | Blueprint can generate; encrypts integration tokens at rest |
| `ADMIN_PASSWORD` | optional | Seeds admin if set |
| `JIRA_EMAIL` | optional | For JIRA API token auth |

**Web**

| Variable | Required | Notes |
|----------|----------|--------|
| `BACKEND_URL` | yes | Public API URL |
| `STORAGE_SECRET` | yes | Blueprint can generate |
| `RELOAD` | `false` | Set by Blueprint |

## Local vs Render

| Concern | Local | Render |
|---------|--------|--------|
| Database | SQLite file | Free Postgres |
| Backend URL | `http://127.0.0.1:8000` | `https://…onrender.com` |
| Bind host | `127.0.0.1` | `0.0.0.0` (auto when `RENDER` is set) |
