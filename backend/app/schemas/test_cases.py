from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ExportFormat, TestCaseType


class TestCase(BaseModel):
    id: str
    title: str
    type: TestCaseType
    steps: list[str]
    expected_result: str


class TestCaseUpdate(BaseModel):
    title: str | None = None
    type: TestCaseType | None = None
    steps: list[str] | None = None
    expected_result: str | None = None


class FilePaths(BaseModel):
    docx: str | None = None
    csv: str | None = None


class TestCaseRunResponse(BaseModel):
    run_id: str
    ticket_key: str
    test_cases: list[TestCase]
    created_at: datetime
    file_paths: FilePaths | None = None
    jira_attached: bool | None = None
    testrail_uploaded: bool | None = None
    testrail_case_ids: list[str] | None = None


class GenerateTestCasesRequest(BaseModel):
    ticket_key: str


class SaveTestCasesRequest(BaseModel):
    folder: str
    formats: list[ExportFormat]


class SaveTestCasesResponse(BaseModel):
    saved_files: list[str]
