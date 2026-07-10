"""Code review orchestration — Git provider → LLM → persist → optional PR post-back."""

from fastapi import Depends

from app.core.errors import not_implemented_yet
from app.integrations.git_provider import GitProviderIntegration, get_git_provider_integration
from app.integrations.llm import LLMIntegration, get_llm_integration
from app.jobs.runner import JobRunner, get_job_runner
from app.schemas.reviews import ReviewCommentUpdate


class CodeReviewService:
    """Orchestrates PR fetch, LLM review, run persistence, and comment triage."""

    def __init__(
        self,
        git: GitProviderIntegration,
        llm: LLMIntegration,
        job_runner: JobRunner,
    ) -> None:
        self._git = git
        self._llm = llm
        self._jobs = job_runner

    async def generate(self, repo: str, pr_number: int):
        # Planned flow: fetch PR → LLM review → persist run + comments
        not_implemented_yet(
            "Code review generation",
            f"Generating AI review for {repo} PR #{pr_number} is not implemented yet. "
            "Orchestration: GitProviderIntegration.fetch_pull_request → LLMIntegration.generate_review.",
        )

    async def get_run(self, run_id: str):
        not_implemented_yet(
            "Review run retrieval",
            f"Fetching review run '{run_id}' is not implemented yet.",
        )

    async def update_comment(self, run_id: str, comment_id: str, update: ReviewCommentUpdate):
        not_implemented_yet(
            "Review comment triage",
            f"Updating comment '{comment_id}' in run '{run_id}' is not implemented yet.",
        )


def get_code_review_service(
    git: GitProviderIntegration = Depends(get_git_provider_integration),
    llm: LLMIntegration = Depends(get_llm_integration),
    job_runner: JobRunner = Depends(get_job_runner),
) -> CodeReviewService:
    return CodeReviewService(git, llm, job_runner)
