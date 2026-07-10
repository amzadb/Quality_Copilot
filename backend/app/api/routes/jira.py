from fastapi import APIRouter, Depends

from app.integrations.jira import JiraIntegration, get_jira_integration
from app.schemas.jira import JiraAttachmentRequest, JiraAttachmentResponse, JiraTicketResponse
from app.services.test_case_service import TestCaseService, get_test_case_service

router = APIRouter()


@router.get("/tickets/{ticket_key}", response_model=JiraTicketResponse)
async def get_jira_ticket(
    ticket_key: str,
    jira: JiraIntegration = Depends(get_jira_integration),
) -> JiraTicketResponse:
    return await jira.fetch_ticket(ticket_key)


@router.post("/tickets/{ticket_key}/attachments", response_model=JiraAttachmentResponse)
async def attach_to_jira(
    ticket_key: str,
    body: JiraAttachmentRequest,
    service: TestCaseService = Depends(get_test_case_service),
) -> JiraAttachmentResponse:
    return await service.attach_to_jira(ticket_key, body)
