from fastapi import APIRouter, Depends

from app.schemas.common import ConnectionTestResponse, IntegrationName
from app.schemas.settings import SettingsResponse, SettingsUpdate
from app.services.settings_service import SettingsService, get_settings_service

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings(service: SettingsService = Depends(get_settings_service)) -> SettingsResponse:
    return await service.get_settings()


@router.put("", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate,
    service: SettingsService = Depends(get_settings_service),
) -> SettingsResponse:
    return await service.update_settings(body)


@router.post("/{integration}/test", response_model=ConnectionTestResponse)
async def test_integration(
    integration: IntegrationName,
    service: SettingsService = Depends(get_settings_service),
) -> ConnectionTestResponse:
    return await service.test_connection(integration)
