from pydantic import BaseModel, Field


class TestRailProject(BaseModel):
    id: int
    name: str


class TestRailSuite(BaseModel):
    id: int
    name: str


class TestRailUploadRequest(BaseModel):
    project_id: int
    suite_id: int | None = None
    new_suite_name: str | None = None


class TestRailUploadResponse(BaseModel):
    suite_id: int
    testrail_case_ids: list[str]
    uploaded_count: int
