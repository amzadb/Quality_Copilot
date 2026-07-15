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
| QA / Integration | 3 | Not started | Full API contract pass + frontend live data |

## Phase 2 deliverables

- [x] `TestCaseService` — JIRA → LLM → DB → local DOCX/CSV → attach / TestRail
- [x] `CodeReviewService` — Git → LLM → DB → triage (`dismissed` / `addressed`)
- [x] `ActivityService` — merged recent activity + metrics summary
- [x] `app/services/exporters.py` — CSV + DOCX writers (`python-docx`)
- [x] Alembic `002_orchestration` — composite PK for cases, `review_runs.duration_seconds`
- [x] Unit tests under `tests/services/` with integrations mocked

## Configuration notes

- **JIRA**: API token + `JIRA_EMAIL` env var (server-side; not in Settings API schema)
- **Bitbucket**: username + app password (Basic auth)
- **Credentials file**: `CREDENTIALS_PATH` (default `./data/credentials.json`)
- **LLM**: Claude API key via Settings; model via `ANTHROPIC_MODEL` (`claude-sonnet-5`)

## Next up — Phase 3

Full pytest + Swagger contract pass; confirm frontend no longer needs demo fallbacks for implemented endpoints.
