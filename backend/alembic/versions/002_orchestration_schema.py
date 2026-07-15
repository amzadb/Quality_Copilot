"""Composite PK for generated cases + review duration.

Revision ID: 002_orchestration
Revises: 001_baseline
Create Date: 2026-07-15

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_orchestration"
down_revision: Union[str, Sequence[str], None] = "001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generated_test_cases_new",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("expected_result", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["test_case_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("run_id", "id"),
    )
    op.execute(
        """
        INSERT INTO generated_test_cases_new (id, run_id, title, type, steps, expected_result)
        SELECT id, run_id, title, type, steps, expected_result FROM generated_test_cases
        """
    )
    op.drop_table("generated_test_cases")
    op.rename_table("generated_test_cases_new", "generated_test_cases")

    op.add_column("review_runs", sa.Column("duration_seconds", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("review_runs", "duration_seconds")

    op.create_table(
        "generated_test_cases_old",
        sa.Column("id", sa.String(length=16), nullable=False),
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("expected_result", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["test_case_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute(
        """
        INSERT INTO generated_test_cases_old (id, run_id, title, type, steps, expected_result)
        SELECT id, run_id, title, type, steps, expected_result FROM generated_test_cases
        """
    )
    op.drop_table("generated_test_cases")
    op.rename_table("generated_test_cases_old", "generated_test_cases")
