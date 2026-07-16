# QA Copilot — Multi-Agent Backend Progress

Track status for the parallel agent implementation plan. Update this file as each phase completes.

| Agent / Task | Phase | Status | Notes |
|---|---|---|---|
| **Foundation** | 0 | **Done** | DB engine/session, Alembic baseline, `.env.example`, `tests/` scaffold |
| **Settings & Credentials** | 1 | **Done** | `CredentialStore`, `SettingsService`, masked GET, file persistence |
| **JIRA Integration** | 1 | **Done** | REST client, fetch/comment/attach, `test_connection` |
| **Git Provider (Bitbucket)** | 1 | **Done** | App-password Basic auth (username + app password); OAuth/Bearer deferred |
| **LLM** | 1 | **Done** | Anthropic Messages API, structured JSON parsing, `test_connection` |
| **TestRail** | 1 | **Done** | Projects/suites/upload, `test_connection` |
| **Test Case Orchestration** | 2 | **Done** | Generate/persist/export/attach/TestRail upload |
| **Code Review Orchestration** | 2 | **Done** | PR fetch → LLM review → persist + comment triage |
| **Dashboard / Activity** | 2 | **Done** | Recent feed + summary from run history |
| **QA / Integration** | 3 | **Done** | Contract tests, OpenAPI coverage, 422 shape, frontend live-API client |
| **User auth & per-user settings** | 4 | **Done** | JWT login/register, admin seed, `user_settings` DB + `credentials.json` fallback, NiceGUI login |

## Phase 3 deliverables

- [x] Full pytest suite green (**54 passed** with auth)
- [x] `tests/api/test_contract.py` — OpenAPI path coverage + end-to-end mocked flow for all contract endpoints
- [x] Validation `422` responses use `{ error: { code, message, details } }`
- [x] Settings responses omit `token` (write-only via `Field(exclude=True)` + `token_set`)
- [x] Frontend client: HTTP errors raise; empty activity kept; connection test never fakes success offline
- [x] Contract copy at [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md)

## Auth & per-user settings

- [x] `User` + `UserSettings` models; Alembic `003_users`
- [x] JWT Bearer auth: register, login, me, logout; protect `/api/v1/*` except auth + `/health`
- [x] Admin seeded only when `ADMIN_PASSWORD` is set (no default password)
- [x] Integration tokens encrypted at rest (`CREDENTIALS_ENCRYPTION_KEY` / Fernet)
- [x] `JWT_SECRET` required (fail closed); ephemeral secret only when `DEBUG=true`
- [x] Authenticated settings from DB; unauthenticated/legacy path uses `credentials.json`
- [x] NiceGUI `/login`, session token in `app.storage.user`, Bearer client, sidebar logout

## Manual Swagger checklist

With backend running (`uvicorn app.main:app --reload --port 8000`), open http://127.0.0.1:8000/docs and verify:

1. `GET/PUT /settings` + `POST /settings/{integration}/test`
2. `GET /jira/tickets/{key}` + attachments
3. Test-case generate → save → download → TestRail upload
4. `GET /pull-requests` → `POST /reviews/generate` → comment triage
5. `GET /activity/recent` + `/summary`

## Configuration notes

- **JIRA**: API token + `JIRA_EMAIL` env var
- **Bitbucket**: username + app password (Basic auth)
- **Credentials file**: `CREDENTIALS_PATH` (default `./data/credentials.json`) — legacy shared fallback only
- **LLM**: Claude API key via Settings; model via `ANTHROPIC_MODEL` (`claude-sonnet-5`)
- **Auth**: set unique `JWT_SECRET` and `CREDENTIALS_ENCRYPTION_KEY` (required when `DEBUG=false`)
- **Admin seed**: opt-in via `ADMIN_PASSWORD` only — no baked-in password
- **Frontend session**: set `STORAGE_SECRET` for NiceGUI `app.storage.user` (do not rely on the code default in shared envs)

## Status: Phase 0–3 + user auth complete

Remaining optional polish (not blockers): dashboard “revisit run” using `GET /test-cases/runs/{id}`, frontend download-file helper, GitHub/GitLab providers, OAuth/SSO.
