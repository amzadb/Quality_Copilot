"""JIRA REST integration — fetch tickets, post comments, attach files."""

from app.core.errors import not_implemented_yet
from app.schemas.common import ConnectionTestResponse
from app.schemas.jira import JiraAttachmentRequest, JiraAttachmentResponse, JiraTicketResponse


class JiraIntegration:
    async def fetch_ticket(self, ticket_key: str) -> JiraTicketResponse:
        not_implemented_yet(
            "JIRA ticket fetch",
            f"Fetching JIRA ticket '{ticket_key}' is not implemented yet.",
        )

    async def post_comment(self, ticket_key: str, comment: str) -> None:
        not_implemented_yet(
            "JIRA comment",
            f"Posting a comment to JIRA ticket '{ticket_key}' is not implemented yet.",
        )

    async def attach_files(
        self, ticket_key: str, body: JiraAttachmentRequest
    ) -> JiraAttachmentResponse:
        not_implemented_yet(
            "JIRA attachment",
            f"Attaching files to JIRA ticket '{ticket_key}' is not implemented yet.",
        )

    async def test_connection(self) -> ConnectionTestResponse:
        not_implemented_yet(
            "JIRA connection test",
            "Testing the JIRA integration is not implemented yet.",
        )


def get_jira_integration() -> JiraIntegration:
    return JiraIntegration()
