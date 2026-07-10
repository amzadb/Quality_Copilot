from pydantic import BaseModel, Field


class JiraTicketResponse(BaseModel):
    key: str
    title: str
    description: str
    acceptance_criteria: list[str] | None = None
    issue_type: str
    url: str


class JiraAttachmentRequest(BaseModel):
    run_id: str
    file_types: list[str] = Field(..., description='Subset of ["docx", "csv"]')
    comment: str | None = None


class JiraAttachmentResponse(BaseModel):
    attached_files: list[str]
    jira_attachment_ids: list[str]
