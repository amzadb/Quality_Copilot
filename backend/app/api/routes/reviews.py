from fastapi import APIRouter, Depends

from app.schemas.reviews import (
    GenerateReviewRequest,
    ReviewComment,
    ReviewCommentUpdate,
    ReviewRunResponse,
)
from app.services.code_review_service import CodeReviewService, get_code_review_service

router = APIRouter()


@router.post("/generate", response_model=ReviewRunResponse)
async def generate_review(
    body: GenerateReviewRequest,
    service: CodeReviewService = Depends(get_code_review_service),
) -> ReviewRunResponse:
    return await service.generate(body.repo, body.pr_number)


@router.get("/runs/{run_id}", response_model=ReviewRunResponse)
async def get_review_run(
    run_id: str,
    service: CodeReviewService = Depends(get_code_review_service),
) -> ReviewRunResponse:
    return await service.get_run(run_id)


@router.patch("/runs/{run_id}/comments/{comment_id}", response_model=ReviewComment)
async def update_review_comment(
    run_id: str,
    comment_id: str,
    body: ReviewCommentUpdate,
    service: CodeReviewService = Depends(get_code_review_service),
) -> ReviewComment:
    return await service.update_comment(run_id, comment_id, body)
