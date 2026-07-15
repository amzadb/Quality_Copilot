# QA Copilot — API Contract (v1)

Spec-level design for the FastAPI backend that the NiceGUI frontend calls. No implementation code — this is the blueprint to build against.

## Conventions

- **Base URL**: `/api/v1`
- **Auth**: JWT Bearer (`Authorization: Bearer <access_token>`). Public: `POST /auth/register`, `POST /auth/login`, and `/health`. All other `/api/v1/*` routes require auth. Integration secrets are stored **per user** in `user_settings` (legacy `credentials.json` only when no user context). Secrets are never returned in full on GET (`token_set` only).
- **Content type**: `application/json` for all requests/responses except file downloads.
- **Error shape** (consistent across all endpoints):
  ```
  {
    "error": {
      "code": "string, e.g. JIRA_NOT_FOUND",
      "message": "human-readable message",
      "details": {} | null
    }
  }
  ```
- **IDs**: internal resources (`TestCaseRun`, `ReviewRun`) use UUIDs. External IDs (JIRA key, PR number, TestRail suite ID) are passed through as-is.
- **Long-running LLM calls**: synchronous for v1 per current design — the HTTP request blocks until the LLM responds. Endpoints that call the LLM are documented with an expected latency note so the frontend knows to show the spinner copy from the mockups.

---

## 0. Auth

### `POST /auth/register`
Create a user + empty settings. Returns `{ access_token, token_type, user }`.

### `POST /auth/login`
Body: `{ "username", "password" }`. Returns the same token envelope as register.

### `GET /auth/me`
Current user (requires Bearer).

### `POST /auth/logout`
No-op server-side for JWT; client clears the token. Requires Bearer.

---

## 1. Settings & integrations

### `GET /settings`
Returns the **current user's** integration config with secrets masked. Requires auth.
**Response**
```
{
  "jira": { "base_url": "acme.atlassian.net", "token_set": true },
  "git_provider": { "type": "bitbucket", "workspace": "acme", "token_set": true },
  "testrail": { "base_url": "acme.testrail.io", "username": "...", "token_set": true },
  "llm": { "provider": "claude", "token_set": true }
}
```

### `PUT /settings`
Updates one or more integration configs. Partial updates allowed — only send the section(s) changed.
**Request**
```
{
  "git_provider": { "type": "bitbucket", "workspace": "acme", "token": "..." }
}
```
**Response**: same shape as `GET /settings` (updated, masked).

### `POST /settings/{integration}/test`
`{integration}` = `jira` | `git_provider` | `testrail` | `llm`. Verifies the stored credentials actually work (test call), used for a "Test connection" affordance in Settings.
**Response**
```
{ "ok": true } | { "ok": false, "error": { "code": "...", "message": "..." } }
```

---

## 2. JIRA tickets

### `GET /jira/tickets/{ticket_key}`
Fetches ticket details for the test-case generation screen.
**Response**
```
{
  "key": "PROJ-1042",
  "title": "Add SSO login flow",
  "description": "...",
  "acceptance_criteria": ["...", "..."] | null,
  "issue_type": "Story",
  "url": "https://acme.atlassian.net/browse/PROJ-1042"
}
```
**Errors**: `JIRA_NOT_FOUND` (404), `JIRA_AUTH_FAILED` (401).

### `POST /jira/tickets/{ticket_key}/attachments`
Attaches file(s) to the ticket — backs the "Attach to JIRA" dialog. Optionally posts a comment.
**Request**
```
{
  "run_id": "uuid",
  "file_types": ["docx"],       // subset of ["docx", "csv"], per checkboxes in dialog
  "comment": "Attaching generated test cases for QA review." | null
}
```
**Response**
```
{ "attached_files": ["PROJ-1042_2026-07-08.docx"], "jira_attachment_ids": ["10021"] }
```

---

## 3. Test case generation

### `POST /test-cases/generate`
Kicks off generation for a ticket. Synchronous — expect 10–60s latency; frontend shows "Generating test cases with Claude…" spinner.
**Request**
```
{ "ticket_key": "PROJ-1042" }
```
**Response**
```
{
  "run_id": "uuid",
  "ticket_key": "PROJ-1042",
  "test_cases": [
    {
      "id": "TC-01",
      "title": "SSO login succeeds with valid credentials",
      "type": "functional",              // functional | edge_case | negative
      "steps": ["...", "..."],
      "expected_result": "..."
    }
  ],
  "created_at": "2026-07-08T10:12:00Z"
}
```
Note: generation always writes local files immediately (see §4) as part of this call — that's the "one generation, two renderers" design from the plan, so `file_paths` is included in the response too:
```
"file_paths": { "docx": "output/test_cases/PROJ-1042_2026-07-08.docx", "csv": "output/test_cases/PROJ-1042_2026-07-08.csv" }
```

### `GET /test-cases/runs/{run_id}`
Fetches a previously generated run (for revisiting from Dashboard "recent activity").
**Response**: same shape as the generate response above, plus `jira_attached`, `testrail_uploaded`, `testrail_case_ids`.

### `PATCH /test-cases/runs/{run_id}/cases/{case_id}`
Edits a single test case after generation (title/steps/expected result), before export/push-back.
**Request**: partial fields to update.
**Response**: the updated test case object.

---

## 4. Local export

### `POST /test-cases/runs/{run_id}/save`
Backs the "Save to local folder" dialog.
**Request**
```
{
  "folder": "output/test_cases/PROJ-1042/",
  "formats": ["docx", "csv"]
}
```
**Response**
```
{ "saved_files": ["output/test_cases/PROJ-1042/PROJ-1042_2026-07-08.docx", "..."] }
```

### `GET /test-cases/runs/{run_id}/download?format=docx|csv`
Streams the file directly (used if the frontend offers a plain download link/button in addition to the save-to-folder flow).

---

## 5. TestRail

### `GET /testrail/projects`
Lists TestRail projects, for the project dropdown in the upload dialog.
**Response**: `[{ "id": 1, "name": "Payments platform" }, ...]`

### `GET /testrail/projects/{project_id}/suites`
Lists existing suites for the "use an existing suite" option.
**Response**: `[{ "id": 12, "name": "Login and authentication" }, ...]`

### `POST /test-cases/runs/{run_id}/testrail-upload`
Uploads all cases in the run to TestRail. Handles both radio-button modes from the dialog.
**Request (existing suite)**
```
{ "project_id": 1, "suite_id": 12 }
```
**Request (new suite)**
```
{ "project_id": 1, "new_suite_name": "SSO login flow" }
```
**Response**
```
{
  "suite_id": 12,
  "testrail_case_ids": ["C1044", "C1045", "..."],
  "uploaded_count": 12
}
```

---

## 6. Pull requests (git provider)

Backed by the `GitProviderClient` abstraction — same contract regardless of whether Bitbucket, GitHub, or GitLab is configured; the active provider comes from Settings.

### `GET /pull-requests?repo=&pr_number=` (or `?url=`)
Fetches PR metadata and diff summary for the code review screen.
**Response**
```
{
  "provider": "bitbucket",
  "repo": "acme/payments",
  "pr_number": 318,
  "title": "Refactor payment retry logic",
  "files_changed": 4,
  "additions": 112,
  "deletions": 48,
  "diff": "..."   // unified diff text, or per-file structured diff — TBD when we hit implementation
}
```

---

## 7. Code review

### `POST /reviews/generate`
Runs the AI review against a fetched PR. Synchronous, ~10–60s latency; "Analyzing diff with Claude…" spinner.
**Request**
```
{ "repo": "acme/payments", "pr_number": 318 }
```
**Response**
```
{
  "run_id": "uuid",
  "pr_number": 318,
  "comments": [
    {
      "file": "retry_handler.py",
      "line": 42,
      "severity": "high",              // high | medium | style
      "comment": "Retry count is not reset after a successful attempt..."
    }
  ],
  "created_at": "2026-07-08T10:20:00Z"
}
```

### `GET /reviews/runs/{run_id}`
Fetches a previously generated review run.

### `PATCH /reviews/runs/{run_id}/comments/{comment_id}`
Marks a comment `dismissed` / `addressed` (for the triage state, even before we build the "post back to PR" push action).

---

## 8. Dashboard

### `GET /activity/recent?limit=20`
Backs the dashboard's recent-activity list — a merged, reverse-chronological feed of test-case runs and review runs.
**Response**
```
[
  { "type": "test_cases", "ticket_key": "PROJ-1042", "title": "Add SSO login flow", "count": 12, "destination": "testrail", "created_at": "..." },
  { "type": "review", "pr_number": 318, "title": "Refactor payment retry logic", "count": 5, "created_at": "..." }
]
```

### `GET /activity/summary`
Backs the four metric cards.
**Response**
```
{ "tickets_processed": 128, "test_cases_generated": 742, "prs_reviewed": 64, "avg_review_time_seconds": 38 }
```

---

## Open items to resolve before implementation

1. **Diff shape** — raw unified diff string vs. structured per-file/per-hunk JSON. Structured is more work up front but makes line-level comment mapping (§7) much more reliable.
2. **Job/run identity for in-flight generation** — since v1 is synchronous, do we still create the `run_id` row *before* the LLM call (so a crash mid-call leaves a "failed" record) or only on success? Recommend the former for auditability.
3. **File naming collisions** — what happens on a second generation for the same ticket on the same day (`PROJ-1042_2026-07-08.docx` already exists)? Suffix with time, or overwrite with a confirmation?
