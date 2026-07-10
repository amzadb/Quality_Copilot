"""Baseline schema for Quality Copilot.

Revision ID: 001_baseline
Revises:
Create Date: 2026-07-10

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tickets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("jira_key", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("acceptance_criteria", sa.JSON(), nullable=True),
        sa.Column("issue_type", sa.String(length=64), nullable=True),
        sa.Column("url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tickets_jira_key"), "tickets", ["jira_key"], unique=True)

    op.create_table(
        "test_case_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ticket_key", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("file_paths", sa.JSON(), nullable=True),
        sa.Column("jira_attached", sa.Boolean(), nullable=False),
        sa.Column("testrail_uploaded", sa.Boolean(), nullable=False),
        sa.Column("testrail_case_ids", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_test_case_runs_ticket_key"), "test_case_runs", ["ticket_key"], unique=False)

    op.create_table(
        "generated_test_cases",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("expected_result", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["test_case_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pull_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("repo", sa.String(length=256), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("files_changed", sa.Integer(), nullable=False),
        sa.Column("additions", sa.Integer(), nullable=False),
        sa.Column("deletions", sa.Integer(), nullable=False),
        sa.Column("diff", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pull_requests_pr_number"), "pull_requests", ["pr_number"], unique=False)
    op.create_index(op.f("ix_pull_requests_repo"), "pull_requests", ["repo"], unique=False)

    op.create_table(
        "review_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("repo", sa.String(length=256), nullable=False),
        sa.Column("pr_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_review_runs_pr_number"), "review_runs", ["pr_number"], unique=False)
    op.create_index(op.f("ix_review_runs_repo"), "review_runs", ["repo"], unique=False)

    op.create_table(
        "review_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("file", sa.String(length=512), nullable=False),
        sa.Column("line", sa.Integer(), nullable=False),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("triage_status", sa.String(length=16), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["review_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_jobs_job_type"), "jobs", ["job_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_jobs_job_type"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("review_comments")
    op.drop_index(op.f("ix_review_runs_repo"), table_name="review_runs")
    op.drop_index(op.f("ix_review_runs_pr_number"), table_name="review_runs")
    op.drop_table("review_runs")
    op.drop_index(op.f("ix_pull_requests_repo"), table_name="pull_requests")
    op.drop_index(op.f("ix_pull_requests_pr_number"), table_name="pull_requests")
    op.drop_table("pull_requests")
    op.drop_table("generated_test_cases")
    op.drop_index(op.f("ix_test_case_runs_ticket_key"), table_name="test_case_runs")
    op.drop_table("test_case_runs")
    op.drop_index(op.f("ix_tickets_jira_key"), table_name="tickets")
    op.drop_table("tickets")
