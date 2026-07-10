"""Test case generation orchestration — JIRA → LLM → export → TestRail."""

from fastapi import Depends

from app.core.errors import not_implemented_yet
from app.integrations.jira import JiraIntegration, get_jira_integration
from app.integrations.llm import LLMIntegration, get_llm_integration
from app.integrations.testrail import TestRailIntegration, get_testrail_integration
from app.jobs.runner import JobRunner, get_job_runner
from app.schemas.jira import JiraAttachmentRequest, JiraAttachmentResponse
from app.schemas.test_cases import SaveTestCasesRequest, SaveTestCasesResponse, TestCaseUpdate
from app.schemas.testrail import TestRailUploadRequest, TestRailUploadResponse


class TestCaseService:
    """Orchestrates ticket fetch, LLM generation, local export, JIRA attach, and TestRail upload."""

    def __init__(
        self,
        jira: JiraIntegration,
        llm: LLMIntegration,
        testrail: TestRailIntegration,
        job_runner: JobRunner,
    ) -> None:
        self._jira = jira
        self._llm = llm
        self._testrail = testrail
        self._jobs = job_runner

    async def generate(self, ticket_key: str):
        # Planned flow: create run → fetch ticket → LLM generate → persist → write files
        not_implemented_yet(
            "Test case generation",
            f"Generating test cases for ticket '{ticket_key}' is not implemented yet. "
            "Orchestration: JiraIntegration.fetch_ticket → LLMIntegration.generate_test_cases → persist run.",
        )

    async def get_run(self, run_id: str):
        not_implemented_yet(
            "Test case run retrieval",
            f"Fetching test case run '{run_id}' is not implemented yet.",
        )

    async def update_case(self, run_id: str, case_id: str, update: TestCaseUpdate):
        not_implemented_yet(
            "Test case edit",
            f"Updating case '{case_id}' in run '{run_id}' is not implemented yet.",
        )

    async def save_to_folder(self, run_id: str, request: SaveTestCasesRequest) -> SaveTestCasesResponse:
        not_implemented_yet(
            "Local export",
            f"Saving test case run '{run_id}' to a local folder is not implemented yet.",
        )

    async def get_download_path(self, run_id: str, format: str):
        not_implemented_yet(
            "File download",
            f"Downloading run '{run_id}' as {format} is not implemented yet.",
        )

    async def attach_to_jira(
        self, ticket_key: str, body: JiraAttachmentRequest
    ) -> JiraAttachmentResponse:
        not_implemented_yet(
            "JIRA attachment",
            f"Attaching files to JIRA ticket '{ticket_key}' is not implemented yet.",
        )

    async def upload_to_testrail(
        self, run_id: str, request: TestRailUploadRequest
    ) -> TestRailUploadResponse:
        not_implemented_yet(
            "TestRail upload",
            f"Uploading test case run '{run_id}' to TestRail is not implemented yet. "
            "Orchestration: load run cases → TestRailIntegration.upload_run.",
        )


def get_test_case_service(
    jira: JiraIntegration = Depends(get_jira_integration),
    llm: LLMIntegration = Depends(get_llm_integration),
    testrail: TestRailIntegration = Depends(get_testrail_integration),
    job_runner: JobRunner = Depends(get_job_runner),
) -> TestCaseService:
    return TestCaseService(jira, llm, testrail, job_runner)
