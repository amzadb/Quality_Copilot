"""LLM integration — prompt templates and structured output parsing."""

from pydantic import BaseModel, Field

from app.core.errors import not_implemented_yet
from app.schemas.common import ConnectionTestResponse, ReviewSeverity, TestCaseType
from app.schemas.jira import JiraTicketResponse
from app.schemas.pull_requests import PullRequestResponse


# --- Structured output models (keep LLM responses honest) ---


class GeneratedTestCase(BaseModel):
    id: str = Field(description="Local case ID, e.g. TC-01")
    title: str
    type: TestCaseType
    steps: list[str]
    expected_result: str


class TestCaseGenerationOutput(BaseModel):
    test_cases: list[GeneratedTestCase]


class GeneratedReviewComment(BaseModel):
    file: str
    line: int
    severity: ReviewSeverity
    comment: str


class CodeReviewOutput(BaseModel):
    comments: list[GeneratedReviewComment]


# --- Prompt templates ---

TEST_CASE_SYSTEM_PROMPT = """\
You are a senior QA engineer. Generate thorough, actionable test cases from a JIRA ticket.
Return JSON matching the TestCaseGenerationOutput schema.
Cover functional, edge-case, and negative scenarios where appropriate.
"""

TEST_CASE_USER_PROMPT = """\
Ticket: {ticket_key}
Title: {title}
Description:
{description}

Acceptance criteria:
{acceptance_criteria}
"""

CODE_REVIEW_SYSTEM_PROMPT = """\
You are a senior code reviewer. Analyze the pull request diff and return structured review comments.
Return JSON matching the CodeReviewOutput schema.
Focus on bugs, reliability issues, and meaningful style concerns.
"""

CODE_REVIEW_USER_PROMPT = """\
Repository: {repo}
PR #{pr_number}: {title}
Files changed: {files_changed} (+{additions}/-{deletions})

Diff:
{diff}
"""


class LLMIntegration:
    async def generate_test_cases(self, ticket: JiraTicketResponse) -> TestCaseGenerationOutput:
        not_implemented_yet(
            "LLM test case generation",
            f"Generating test cases for ticket '{ticket.key}' via LLM is not implemented yet.",
        )

    async def generate_review(self, pull_request: PullRequestResponse) -> CodeReviewOutput:
        not_implemented_yet(
            "LLM code review",
            f"Generating AI review for PR #{pull_request.pr_number} is not implemented yet.",
        )

    async def test_connection(self) -> ConnectionTestResponse:
        not_implemented_yet(
            "LLM connection test",
            "Testing the LLM provider integration is not implemented yet.",
        )


def get_llm_integration() -> LLMIntegration:
    return LLMIntegration()
