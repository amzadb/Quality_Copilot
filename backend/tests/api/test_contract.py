"""API contract integration tests — shapes, status codes, and OpenAPI coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.integrations.git_provider import get_git_provider_integration
from app.integrations.jira import get_jira_integration
from app.integrations.llm import (
    CodeReviewOutput,
    GeneratedReviewComment,
    GeneratedTestCase,
    TestCaseGenerationOutput,
    get_llm_integration,
)
from app.integrations.testrail import get_testrail_integration
from app.main import app
from app.models import Base
from app.models.base import get_db
from app.schemas.common import ConnectionTestSuccess
from app.schemas.jira import JiraAttachmentResponse, JiraTicketResponse
from app.schemas.pull_requests import PullRequestResponse
from app.schemas.testrail import TestRailProject, TestRailSuite, TestRailUploadResponse


CONTRACT_PATHS = {
    ("POST", "/api/v1/auth/register"),
    ("POST", "/api/v1/auth/login"),
    ("GET", "/api/v1/auth/me"),
    ("POST", "/api/v1/auth/logout"),
    ("GET", "/api/v1/settings"),
    ("PUT", "/api/v1/settings"),
    ("POST", "/api/v1/settings/{integration}/test"),
    ("GET", "/api/v1/jira/tickets/{ticket_key}"),
    ("POST", "/api/v1/jira/tickets/{ticket_key}/attachments"),
    ("POST", "/api/v1/test-cases/generate"),
    ("GET", "/api/v1/test-cases/runs/{run_id}"),
    ("PATCH", "/api/v1/test-cases/runs/{run_id}/cases/{case_id}"),
    ("POST", "/api/v1/test-cases/runs/{run_id}/save"),
    ("GET", "/api/v1/test-cases/runs/{run_id}/download"),
    ("POST", "/api/v1/test-cases/runs/{run_id}/testrail-upload"),
    ("GET", "/api/v1/testrail/projects"),
    ("GET", "/api/v1/testrail/projects/{project_id}/suites"),
    ("GET", "/api/v1/pull-requests"),
    ("POST", "/api/v1/reviews/generate"),
    ("GET", "/api/v1/reviews/runs/{run_id}"),
    ("PATCH", "/api/v1/reviews/runs/{run_id}/comments/{comment_id}"),
    ("GET", "/api/v1/activity/recent"),
    ("GET", "/api/v1/activity/summary"),
}


@pytest.fixture
def api_env(tmp_path, monkeypatch):
    db_path = tmp_path / "contract.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    cred_path = tmp_path / "credentials.json"
    monkeypatch.setattr("app.config.settings.credentials_path", str(cred_path))
    monkeypatch.setattr("app.config.settings.jira_email", "qa@example.com")
    from app.core.credential_store import reset_credential_store

    reset_credential_store(cred_path)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    jira = AsyncMock()
    git = AsyncMock()
    llm = AsyncMock()
    testrail = AsyncMock()

    jira.fetch_ticket.return_value = JiraTicketResponse(
        key="PROJ-1042",
        title="Add SSO login flow",
        description="Users authenticate via SSO.",
        issue_type="Story",
        url="https://acme.atlassian.net/browse/PROJ-1042",
    )
    jira.attach_files.return_value = JiraAttachmentResponse(
        attached_files=["PROJ-1042.docx"],
        jira_attachment_ids=["10021"],
    )
    jira.test_connection.return_value = ConnectionTestSuccess()
    git.test_connection.return_value = ConnectionTestSuccess()
    llm.test_connection.return_value = ConnectionTestSuccess()
    testrail.test_connection.return_value = ConnectionTestSuccess()

    git.fetch_pull_request.return_value = PullRequestResponse(
        provider="bitbucket",
        repo="acme/payments",
        pr_number=318,
        title="Refactor payment retry logic",
        files_changed=2,
        additions=10,
        deletions=3,
        diff="diff --git a/a.py b/a.py\n",
    )
    llm.generate_test_cases.return_value = TestCaseGenerationOutput(
        test_cases=[
            GeneratedTestCase(
                id="TC-01",
                title="SSO login succeeds",
                type="functional",
                steps=["Open login"],
                expected_result="Dashboard loads.",
            )
        ]
    )
    llm.generate_review.return_value = CodeReviewOutput(
        comments=[
            GeneratedReviewComment(
                file="retry.py",
                line=42,
                severity="high",
                comment="Retry count is not reset.",
            )
        ]
    )
    testrail.list_projects.return_value = [TestRailProject(id=1, name="Payments platform")]
    testrail.list_suites.return_value = [TestRailSuite(id=12, name="Login")]
    testrail.upload_run.return_value = TestRailUploadResponse(
        suite_id=12,
        testrail_case_ids=["C1044"],
        uploaded_count=1,
    )

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_jira_integration] = lambda: jira
    app.dependency_overrides[get_git_provider_integration] = lambda: git
    app.dependency_overrides[get_llm_integration] = lambda: llm
    app.dependency_overrides[get_testrail_integration] = lambda: testrail

    monkeypatch.chdir(tmp_path)
    client = TestClient(app)
    register = client.post(
        "/api/v1/auth/register",
        json={"username": "contract", "password": "secret12", "email": "c@example.com"},
    )
    assert register.status_code == 200, register.text
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}
    try:
        yield client, headers, jira, git, llm, testrail
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_openapi_covers_contract_paths(api_env):
    client, *_ = api_env
    schema = client.get("/openapi.json").json()
    found: set[tuple[str, str]] = set()
    for path, methods in schema["paths"].items():
        for method in methods:
            if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                found.add((method.upper(), path))
    missing = CONTRACT_PATHS - found
    assert not missing, f"Missing from OpenAPI: {missing}"


def test_validation_error_matches_contract_shape(api_env):
    client, headers, *_ = api_env
    response = client.post("/api/v1/test-cases/generate", headers=headers, json={})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "message" in body["error"]


def test_settings_masks_tokens(api_env):
    client, headers, *_ = api_env
    put = client.put(
        "/api/v1/settings",
        headers=headers,
        json={"jira": {"base_url": "acme.atlassian.net", "token": "secret-token"}},
    )
    assert put.status_code == 200
    body = put.json()
    assert body["jira"]["token_set"] is True
    assert "token" not in body["jira"]

    get = client.get("/api/v1/settings", headers=headers)
    assert get.status_code == 200
    assert "token" not in get.json()["jira"]


def test_settings_connection_test(api_env):
    client, headers, *_ = api_env
    response = client.post("/api/v1/settings/jira/test", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_full_test_case_and_review_flow(api_env):
    client, headers, jira, git, llm, testrail = api_env

    ticket = client.get("/api/v1/jira/tickets/PROJ-1042", headers=headers)
    assert ticket.status_code == 200
    assert ticket.json()["key"] == "PROJ-1042"

    generated = client.post(
        "/api/v1/test-cases/generate",
        headers=headers,
        json={"ticket_key": "PROJ-1042"},
    )
    assert generated.status_code == 200
    run = generated.json()
    assert run["ticket_key"] == "PROJ-1042"
    assert run["test_cases"][0]["id"] == "TC-01"
    assert run["file_paths"]["docx"]
    run_id = run["run_id"]

    patched = client.patch(
        f"/api/v1/test-cases/runs/{run_id}/cases/TC-01",
        headers=headers,
        json={"title": "Updated SSO case"},
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "Updated SSO case"

    saved = client.post(
        f"/api/v1/test-cases/runs/{run_id}/save",
        headers=headers,
        json={"folder": "exports/PROJ-1042", "formats": ["csv"]},
    )
    assert saved.status_code == 200
    assert saved.json()["saved_files"]

    download = client.get(
        f"/api/v1/test-cases/runs/{run_id}/download?format=csv",
        headers=headers,
    )
    assert download.status_code == 200
    assert "text/csv" in download.headers["content-type"]

    attached = client.post(
        "/api/v1/jira/tickets/PROJ-1042/attachments",
        headers=headers,
        json={"run_id": run_id, "file_types": ["docx"], "comment": "QA cases"},
    )
    assert attached.status_code == 200
    assert attached.json()["jira_attachment_ids"] == ["10021"]
    jira.attach_files.assert_awaited()

    projects = client.get("/api/v1/testrail/projects", headers=headers)
    assert projects.status_code == 200
    assert projects.json()[0]["id"] == 1

    suites = client.get("/api/v1/testrail/projects/1/suites", headers=headers)
    assert suites.status_code == 200
    assert suites.json()[0]["id"] == 12

    uploaded = client.post(
        f"/api/v1/test-cases/runs/{run_id}/testrail-upload",
        headers=headers,
        json={"project_id": 1, "suite_id": 12},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["uploaded_count"] == 1

    pr = client.get(
        "/api/v1/pull-requests?repo=acme/payments&pr_number=318",
        headers=headers,
    )
    assert pr.status_code == 200
    assert pr.json()["pr_number"] == 318

    review = client.post(
        "/api/v1/reviews/generate",
        headers=headers,
        json={"repo": "acme/payments", "pr_number": 318},
    )
    assert review.status_code == 200
    review_body = review.json()
    assert review_body["pr_number"] == 318
    comment_id = review_body["comments"][0]["id"]

    triaged = client.patch(
        f"/api/v1/reviews/runs/{review_body['run_id']}/comments/{comment_id}",
        headers=headers,
        json={"triage_status": "addressed"},
    )
    assert triaged.status_code == 200
    assert triaged.json()["triage_status"] == "addressed"

    recent = client.get("/api/v1/activity/recent?limit=10", headers=headers)
    assert recent.status_code == 200
    assert isinstance(recent.json(), list)
    assert len(recent.json()) >= 2

    summary = client.get("/api/v1/activity/summary", headers=headers)
    assert summary.status_code == 200
    body = summary.json()
    assert body["tickets_processed"] >= 1
    assert body["test_cases_generated"] >= 1
    assert body["prs_reviewed"] >= 1
    assert "avg_review_time_seconds" in body


def test_app_error_shape_for_not_found(api_env):
    client, headers, *_ = api_env
    response = client.get(
        "/api/v1/test-cases/runs/00000000-0000-0000-0000-000000000099",
        headers=headers,
    )
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "RUN_NOT_FOUND"
    assert "message" in body["error"]
