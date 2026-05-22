from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.core.tenant import TenantContext
from app.schemas.settings import (
    TutorConnectionTestResponse,
    TutorSettingsResponse,
    TutorSettingsUpdate,
)
from app.services.tutor_settings_service import TutorSettingsService

router = APIRouter(prefix="/settings/tutor", tags=["settings"])


def get_tutor_settings_service(
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> TutorSettingsService:
    return TutorSettingsService(db, tenant)


@router.get("", response_model=TutorSettingsResponse)
def get_tutor_settings(
    service: Annotated[TutorSettingsService, Depends(get_tutor_settings_service)],
) -> TutorSettingsResponse:
    return service.get_settings()


@router.put("", response_model=TutorSettingsResponse)
def save_tutor_settings(
    settings: TutorSettingsUpdate,
    service: Annotated[TutorSettingsService, Depends(get_tutor_settings_service)],
) -> TutorSettingsResponse:
    return service.save_settings(settings)


@router.post("/test", response_model=TutorConnectionTestResponse)
def test_tutor_settings(
    settings: TutorSettingsUpdate,
    service: Annotated[TutorSettingsService, Depends(get_tutor_settings_service)],
) -> TutorConnectionTestResponse:
    return service.test_settings(settings)
