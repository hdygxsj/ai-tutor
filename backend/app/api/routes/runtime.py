from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_session, get_tenant_context
from app.core.tenant import TenantContext
from app.schemas.runtime import RuntimeSettingsResponse, RuntimeSettingsUpdate
from app.services.runtime_settings_service import RuntimeSettingsService

router = APIRouter(prefix="/runtime", tags=["runtime"])


def get_runtime_settings_service(
    db: Annotated[Session, Depends(get_session)],
    tenant: Annotated[TenantContext, Depends(get_tenant_context)],
) -> RuntimeSettingsService:
    return RuntimeSettingsService(db, tenant)


@router.get("/settings", response_model=RuntimeSettingsResponse)
def get_runtime_settings(
    service: Annotated[RuntimeSettingsService, Depends(get_runtime_settings_service)],
) -> RuntimeSettingsResponse:
    return service.get_settings()


@router.put("/settings", response_model=RuntimeSettingsResponse)
def save_runtime_settings(
    update: RuntimeSettingsUpdate,
    service: Annotated[RuntimeSettingsService, Depends(get_runtime_settings_service)],
) -> RuntimeSettingsResponse:
    return service.save_settings(update)
