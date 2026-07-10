from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.schemas.common import ExportFormat
from app.schemas.test_cases import (
    GenerateTestCasesRequest,
    SaveTestCasesRequest,
    SaveTestCasesResponse,
    TestCase,
    TestCaseRunResponse,
    TestCaseUpdate,
)
from app.schemas.testrail import TestRailUploadRequest, TestRailUploadResponse
from app.services.test_case_service import TestCaseService, get_test_case_service

router = APIRouter()


@router.post("/generate", response_model=TestCaseRunResponse)
async def generate_test_cases(
    body: GenerateTestCasesRequest,
    service: TestCaseService = Depends(get_test_case_service),
) -> TestCaseRunResponse:
    return await service.generate(body.ticket_key)


@router.get("/runs/{run_id}", response_model=TestCaseRunResponse)
async def get_test_case_run(
    run_id: str,
    service: TestCaseService = Depends(get_test_case_service),
) -> TestCaseRunResponse:
    return await service.get_run(run_id)


@router.patch("/runs/{run_id}/cases/{case_id}", response_model=TestCase)
async def update_test_case(
    run_id: str,
    case_id: str,
    body: TestCaseUpdate,
    service: TestCaseService = Depends(get_test_case_service),
) -> TestCase:
    return await service.update_case(run_id, case_id, body)


@router.post("/runs/{run_id}/save", response_model=SaveTestCasesResponse)
async def save_test_cases(
    run_id: str,
    body: SaveTestCasesRequest,
    service: TestCaseService = Depends(get_test_case_service),
) -> SaveTestCasesResponse:
    return await service.save_to_folder(run_id, body)


@router.get("/runs/{run_id}/download")
async def download_test_cases(
    run_id: str,
    format: ExportFormat,
    service: TestCaseService = Depends(get_test_case_service),
) -> FileResponse:
    path = await service.get_download_path(run_id, format)
    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if format == "docx"
        else "text/csv"
    )
    return FileResponse(path=path, media_type=media_type, filename=path.split("/")[-1])


@router.post("/runs/{run_id}/testrail-upload", response_model=TestRailUploadResponse)
async def upload_to_testrail(
    run_id: str,
    body: TestRailUploadRequest,
    service: TestCaseService = Depends(get_test_case_service),
) -> TestRailUploadResponse:
    return await service.upload_to_testrail(run_id, body)
