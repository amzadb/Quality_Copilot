from fastapi import APIRouter, Depends

from app.integrations.testrail import TestRailIntegration, get_testrail_integration
from app.schemas.testrail import TestRailProject, TestRailSuite

router = APIRouter()


@router.get("/projects", response_model=list[TestRailProject])
async def list_testrail_projects(
    testrail: TestRailIntegration = Depends(get_testrail_integration),
) -> list[TestRailProject]:
    return await testrail.list_projects()


@router.get("/projects/{project_id}/suites", response_model=list[TestRailSuite])
async def list_testrail_suites(
    project_id: int,
    testrail: TestRailIntegration = Depends(get_testrail_integration),
) -> list[TestRailSuite]:
    return await testrail.list_suites(project_id)
