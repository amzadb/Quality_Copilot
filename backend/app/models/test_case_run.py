import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TestCaseRun(Base):
    __tablename__ = "test_case_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ticket_key: Mapped[str] = mapped_column(String(32), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    file_paths: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    jira_attached: Mapped[bool] = mapped_column(Boolean, default=False)
    testrail_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)
    testrail_case_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    test_cases: Mapped[list["GeneratedTestCase"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class GeneratedTestCase(Base):
    __tablename__ = "generated_test_cases"

    id: Mapped[str] = mapped_column(String(16), primary_key=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_case_runs.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(512))
    type: Mapped[str] = mapped_column(String(32))
    steps: Mapped[list] = mapped_column(JSON)
    expected_result: Mapped[str] = mapped_column(Text)

    run: Mapped[TestCaseRun] = relationship(back_populates="test_cases")
