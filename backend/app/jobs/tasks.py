"""Named background tasks invoked by the job runner.

Phase 2 keeps LLM generation synchronous. These helpers are available for
future async export/upload/post-back work once JobRunner usage expands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import UUID

from app.models.base import SessionLocal
from app.models.test_case_run import GeneratedTestCase, TestCaseRun
from app.schemas.test_cases import TestCase
from app.services.exporters import export_cases


async def export_test_cases_to_folder(
    run_id: str,
    folder: str,
    formats: list[str],
    *,
    job_id: str | None = None,
) -> dict[str, Any]:
    db = SessionLocal()
    try:
        run = db.get(TestCaseRun, UUID(run_id))
        if run is None:
            return {"job_id": job_id, "ok": False, "error": "RUN_NOT_FOUND"}
        cases = [
            TestCase(
                id=case.id,
                title=case.title,
                type=case.type,  # type: ignore[arg-type]
                steps=list(case.steps),
                expected_result=case.expected_result,
            )
            for case in db.query(GeneratedTestCase).filter_by(run_id=run.id).all()
        ]
        saved = export_cases(Path(folder), run.ticket_key, cases, formats)
        paths = dict(run.file_paths or {})
        paths.update(saved)
        run.file_paths = paths
        db.commit()
        return {"job_id": job_id, "ok": True, "saved_files": list(saved.values())}
    finally:
        db.close()
