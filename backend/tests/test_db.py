"""Database foundation tests."""

import uuid

from app.models import GeneratedTestCase, Job, PullRequestRecord, ReviewRun, Ticket
from app.models.test_case_run import TestCaseRun as TestCaseRunModel


def test_metadata_creates_all_tables(db_engine):
    from sqlalchemy import inspect

    table_names = set(inspect(db_engine).get_table_names())
    expected = {
        "tickets",
        "test_case_runs",
        "generated_test_cases",
        "pull_requests",
        "review_runs",
        "review_comments",
        "jobs",
    }
    assert expected.issubset(table_names)


def test_session_persists_ticket(db_session):
    ticket = Ticket(
        jira_key="PROJ-1042",
        title="Add SSO login flow",
        description="Users authenticate via company SSO.",
    )
    db_session.add(ticket)
    db_session.commit()

    stored = db_session.query(Ticket).filter_by(jira_key="PROJ-1042").one()
    assert stored.title == "Add SSO login flow"
    assert stored.id is not None


def test_test_case_run_relationship(db_session):
    run = TestCaseRunModel(ticket_key="PROJ-1042", status="completed")
    run.test_cases.append(
        GeneratedTestCase(
            id="TC-01",
            title="SSO login succeeds",
            type="functional",
            steps=["Navigate to login", "Click SSO"],
            expected_result="User reaches dashboard.",
        )
    )
    db_session.add(run)
    db_session.commit()

    stored = db_session.get(TestCaseRunModel, run.id)
    assert stored is not None
    assert len(stored.test_cases) == 1
    assert stored.test_cases[0].id == "TC-01"


def test_baseline_migration_creates_expected_tables(migrated_db_path):
    _, inspector = migrated_db_path
    table_names = set(inspector.get_table_names())

    assert table_names == {
        "alembic_version",
        "tickets",
        "test_case_runs",
        "generated_test_cases",
        "pull_requests",
        "review_runs",
        "review_comments",
        "jobs",
    }


def test_job_record_round_trip(db_session):
    job = Job(
        id=uuid.uuid4(),
        job_type="export_test_cases",
        status="queued",
        payload={"run_id": str(uuid.uuid4())},
    )
    db_session.add(job)
    db_session.commit()

    stored = db_session.get(Job, job.id)
    assert stored is not None
    assert stored.job_type == "export_test_cases"


def test_pull_request_and_review_run_persist(db_session):
    pr = PullRequestRecord(
        provider="bitbucket",
        repo="acme/payments",
        pr_number=318,
        title="Refactor payment retry logic",
        files_changed=4,
        additions=112,
        deletions=48,
    )
    review = ReviewRun(repo="acme/payments", pr_number=318, status="completed")
    db_session.add_all([pr, review])
    db_session.commit()

    assert db_session.get(PullRequestRecord, pr.id) is not None
    assert db_session.get(ReviewRun, review.id) is not None
